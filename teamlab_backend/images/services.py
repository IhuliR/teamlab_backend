import logging
import uuid
from datetime import timedelta
from functools import partial

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)

from .models import ImageUpload
from .exceptions import StorageUnavailable
from projects.models import Project
from users.models import PortfolioWork


logger = logging.getLogger(__name__)


def generate_upload_url(
    key: str,
    content_type: str,
    max_size: int,
) -> dict:
    options = settings.STORAGES['media_s3']['OPTIONS']
    s3 = boto3.client(
        's3',
        endpoint_url=options['endpoint_url'],
        region_name=options['region_name'],
    )

    return s3.generate_presigned_post(
        Bucket=options['bucket_name'],
        Key=key,
        Fields={
            'Content-Type': content_type,
        },
        Conditions=[
            {'Content-Type': content_type},
            [
                'content-length-range',
                1,
                max_size + settings.IMAGE_PRESIGNED_POST_OVERHEAD_BYTES,
            ],
        ],
        ExpiresIn=settings.IMAGE_PRESIGN_TTL_SECONDS,
    )


def get_upload_target(*, kind, target_id, user, for_update=False):
    target_fields = {
        'project': None,
        'portfolio_work': None,
    }

    if kind == ImageUpload.Kind.PROJECT_IMAGE:
        queryset = Project.objects.all()

        if for_update:
            queryset = queryset.select_for_update()

        project = get_object_or_404(queryset, pk=target_id)

        if project.owner_id != user.pk:
            raise PermissionDenied('Нет прав на изменение проекта.')

        target_fields['project'] = project

    elif kind == ImageUpload.Kind.PORTFOLIO_IMAGE:
        queryset = PortfolioWork.objects.all()

        if for_update:
            queryset = queryset.select_for_update()

        work = get_object_or_404(queryset, pk=target_id)

        if work.user_id != user.pk:
            raise PermissionDenied('Нет прав на изменение портфолио.')

        target_fields['portfolio_work'] = work

    return target_fields


def create_image_upload(*, user, validated_data):
    kind = validated_data['kind']
    target_id = validated_data.get('target_id')

    get_upload_target(
        kind=kind,
        target_id=target_id,
        user=user,
    )

    upload_id = uuid.uuid4()
    temporary_key = f'temporary/{upload_id}/image'

    try:
        presigned = generate_upload_url(
            key=temporary_key,
            content_type=validated_data['content_type'],
            max_size=settings.IMAGE_UPLOAD_LIMITS[kind],
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageUnavailable() from exc

    with transaction.atomic():
        target_fields = get_upload_target(
            kind=kind,
            target_id=target_id,
            user=user,
            for_update=True,
        )

        upload = ImageUpload.objects.create(
            id=upload_id,
            owner=user,
            kind=kind,
            temporary_key=temporary_key,
            declared_size=validated_data['size_bytes'],
            declared_content_type=validated_data['content_type'],
            expires_at=timezone.now() + timedelta(
                seconds=settings.IMAGE_PRESIGN_TTL_SECONDS,
            ),
            **target_fields,
        )

    return upload, presigned


def get_uploaded_object_metadata(key: str) -> dict:
    options = settings.STORAGES['media_s3']['OPTIONS']
    s3 = boto3.client(
        's3',
        endpoint_url=options['endpoint_url'],
        region_name=options['region_name'],
    )

    return s3.head_object(
        Bucket=options['bucket_name'],
        Key=key,
    )


def validate_upload_confirmation(upload: ImageUpload) -> bool:
    if upload.status == ImageUpload.Status.QUEUED:
        return False

    if upload.status != ImageUpload.Status.AWAITING_UPLOAD:
        raise ValidationError({
            'status': 'Загрузка недоступна для подтверждения.',
        })

    if upload.expires_at <= timezone.now():
        raise ValidationError({
            'expires_at': 'Срок действия загрузки истёк.',
        })

    return True


def dispatch_image_processing(*, upload_id, dispatched_at):
    from .tasks import process_uploaded_image

    try:
        process_uploaded_image.delay(str(upload_id))
    except Exception:
        ImageUpload.objects.filter(
            pk=upload_id,
            status=ImageUpload.Status.QUEUED,
            last_dispatched_at=dispatched_at,
        ).update(last_dispatched_at=None)
        logger.exception(
            'Не удалось отправить изображение %s на обработку.',
            upload_id,
        )


def confirm_image_upload(*, user, upload_id):
    upload = get_object_or_404(
        ImageUpload,
        id=upload_id,
        owner=user,
    )
    if not validate_upload_confirmation(upload):
        return upload

    try:
        metadata = get_uploaded_object_metadata(
            key=upload.temporary_key,
        )
    except ClientError as exc:
        error = exc.response.get('Error', {})
        error_code = error.get('Code')

        if error_code in ('404', 'NoSuchKey', 'NotFound'):
            raise ValidationError({
                'file': 'Файл ещё не загружен в S3.',
            }) from exc

        raise StorageUnavailable() from exc

    except BotoCoreError as exc:
        raise StorageUnavailable() from exc

    actual_size = metadata['ContentLength']
    actual_content_type = metadata['ContentType']

    if (
        actual_size <= 0
        or actual_size != upload.declared_size
        or actual_size > settings.IMAGE_UPLOAD_LIMITS[upload.kind]
    ):
        raise ValidationError({
            'size_bytes': 'Фактический размер файла '
                          'не соответствует требованиям.',
        })

    if actual_content_type != upload.declared_content_type:
        raise ValidationError({
            'content_type': 'MIME-тип файла не совпадает с заявленным.',
        })

    with transaction.atomic():

        upload = get_object_or_404(
            ImageUpload.objects.select_for_update(),
            pk=upload.pk,
            owner=user,
        )

        if not validate_upload_confirmation(upload):
            return upload

        upload.actual_size = actual_size
        upload.actual_content_type = actual_content_type
        upload.etag = metadata['ETag']
        upload.status = ImageUpload.Status.QUEUED
        dispatched_at = timezone.now()
        upload.last_dispatched_at = dispatched_at
        upload.save(
            update_fields=[
                'actual_size',
                'actual_content_type',
                'etag',
                'status',
                'last_dispatched_at',
            ],
        )
        transaction.on_commit(partial(
            dispatch_image_processing,
            upload_id=upload.pk,
            dispatched_at=dispatched_at,
        ))

    return upload


def download_image(
    *,
    key: str,
    max_size: int,
    expected_etag: str,
    expected_size: int,
) -> bytes:
    options = settings.STORAGES['media_s3']['OPTIONS']

    s3 = boto3.client(
        's3',
        endpoint_url=options['endpoint_url'],
        region_name=options['region_name'],
    )
    response = s3.get_object(
        Bucket=options['bucket_name'],
        Key=key,
        IfMatch=expected_etag,
    )
    body = response['Body']

    try:
        content_length = response['ContentLength']
        if content_length != expected_size or content_length > max_size:
            raise ValueError('Размер файла не соответствует подтверждённому.')

        data = body.read(max_size + 1)

        if len(data) != content_length:
            raise ValueError('Недопустимый размер файла.')

        return data

    finally:
        body.close()


def save_processed_image(*, key: str, image_bytes: bytes) -> str:
    storage = storages['media_s3']
    content = ContentFile(image_bytes)
    content.content_type = 'image/webp'
    return storage.save(key, content)


def _delete_local_file_safely(*, storage, name: str) -> None:
    try:
        storage.delete(name)
    except Exception:
        logger.exception('Не удалось удалить локальный медиафайл %s.', name)


def _schedule_local_file_deletion(field_file, *, new_name=None) -> None:
    if not field_file or not field_file.name or field_file.name == new_name:
        return

    transaction.on_commit(partial(
        _delete_local_file_safely,
        storage=field_file.storage,
        name=field_file.name,
    ))


def dispatch_superseded_cleanup(*, upload_id) -> None:
    from .tasks import delete_superseded_image

    try:
        delete_superseded_image.delay(str(upload_id))
    except Exception:
        logger.exception(
            'Не удалось отправить удаление изображения %s.',
            upload_id,
        )


def _schedule_superseded_cleanup(upload_id) -> None:
    if upload_id is None:
        return

    transaction.on_commit(partial(
        dispatch_superseded_cleanup,
        upload_id=upload_id,
    ))


def _supersede_upload(upload_id) -> bool:
    if upload_id is None:
        return False

    updated = ImageUpload.objects.filter(
        pk=upload_id,
        status=ImageUpload.Status.ATTACHED,
    ).update(status=ImageUpload.Status.SUPERSEDED)

    if updated:
        _schedule_superseded_cleanup(upload_id)

    return bool(updated)


def _target_configuration(target):
    User = get_user_model()

    if isinstance(target, User):
        return User, 'avatar', 'avatar_upload', 'self'
    if isinstance(target, Project):
        return Project, 'image', 'image_upload', 'owner_id'
    if isinstance(target, PortfolioWork):
        return PortfolioWork, 'image', 'image_upload', 'user_id'

    raise TypeError('Неподдерживаемая сущность изображения.')


def _lock_image_target(*, target, user):
    model, image_field, upload_field, owner_field = _target_configuration(
        target,
    )
    locked_target = get_object_or_404(
        model.objects.select_for_update(),
        pk=target.pk,
    )

    if owner_field == 'self':
        allowed = locked_target.pk == user.pk
    else:
        allowed = getattr(locked_target, owner_field) == user.pk

    if not allowed:
        raise PermissionDenied('Нет прав на изменение изображения.')

    return locked_target, image_field, upload_field


def _save_image_target(target, *fields) -> None:
    update_fields = list(fields)
    if hasattr(target, 'updated_at'):
        update_fields.append('updated_at')
    target.save(update_fields=update_fields)


def attach_image_upload(*, user, upload_id) -> ImageUpload:
    candidate = get_object_or_404(
        ImageUpload.objects.only(
            'id',
            'owner_id',
            'kind',
            'project_id',
            'portfolio_work_id',
        ),
        pk=upload_id,
        owner=user,
    )
    User = get_user_model()

    if candidate.kind == ImageUpload.Kind.USER_AVATAR:
        target = user
        expected_target_field = None
    elif candidate.kind == ImageUpload.Kind.PROJECT_IMAGE:
        if candidate.project_id is None:
            raise ValidationError({'target': 'Проект загрузки не найден.'})
        target = get_object_or_404(Project, pk=candidate.project_id)
        expected_target_field = 'project_id'
    elif candidate.kind == ImageUpload.Kind.PORTFOLIO_IMAGE:
        if candidate.portfolio_work_id is None:
            raise ValidationError({
                'target': 'Работа портфолио загрузки не найдена.',
            })
        target = get_object_or_404(
            PortfolioWork,
            pk=candidate.portfolio_work_id,
        )
        expected_target_field = 'portfolio_work_id'
    else:
        raise ValidationError({'kind': 'Недопустимый тип изображения.'})

    with transaction.atomic():
        target, image_field, upload_field = _lock_image_target(
            target=target,
            user=user,
        )
        upload = get_object_or_404(
            ImageUpload.objects.select_for_update(),
            pk=upload_id,
            owner=user,
        )

        if upload.kind != candidate.kind:
            raise ValidationError({'kind': 'Тип загрузки изменился.'})
        if expected_target_field is None:
            valid_target = (
                upload.project_id is None
                and upload.portfolio_work_id is None
                and isinstance(target, User)
            )
        else:
            valid_target = (
                getattr(upload, expected_target_field)
                == target.pk
            )

        if not valid_target:
            raise ValidationError({
                'target': 'Изображение предназначено другой сущности.',
            })

        current_upload_id = getattr(target, f'{upload_field}_id')
        if (
            current_upload_id == upload.pk
            and upload.status == ImageUpload.Status.ATTACHED
        ):
            return upload

        if upload.status != ImageUpload.Status.READY:
            raise ValidationError({
                'status': 'Изображение ещё не готово к привязке.',
            })
        if not upload.final_key or not upload.thumbnail_key:
            raise ValidationError({
                'status': 'Обработка изображения завершена некорректно.',
            })

        previous_local_file = getattr(target, image_field)
        setattr(target, upload_field, upload)
        setattr(target, image_field, None)
        _save_image_target(target, upload_field, image_field)

        upload.status = ImageUpload.Status.ATTACHED
        upload.save(update_fields=['status'])

        if current_upload_id and current_upload_id != upload.pk:
            _supersede_upload(current_upload_id)

        _schedule_local_file_deletion(previous_local_file)

    return upload


def attach_user_avatar(*, user_id, upload_id) -> ImageUpload:
    User = get_user_model()
    user = get_object_or_404(User, pk=user_id)
    return attach_image_upload(user=user, upload_id=upload_id)


def attach_target_image(*, user, upload_id) -> ImageUpload:
    return attach_image_upload(user=user, upload_id=upload_id)


def replace_image_with_local(*, target, user, image):
    with transaction.atomic():
        target, image_field, upload_field = _lock_image_target(
            target=target,
            user=user,
        )
        previous_upload_id = getattr(target, f'{upload_field}_id')
        previous_local_file = getattr(target, image_field)

        setattr(target, upload_field, None)
        setattr(target, image_field, image)
        _save_image_target(target, upload_field, image_field)

        _supersede_upload(previous_upload_id)
        new_name = getattr(target, image_field).name
        _schedule_local_file_deletion(
            previous_local_file,
            new_name=new_name,
        )

    return target


def detach_image(*, target, user) -> None:
    replace_image_with_local(target=target, user=user, image=None)


def delete_portfolio_work(*, work, user) -> None:
    with transaction.atomic():
        work, image_field, upload_field = _lock_image_target(
            target=work,
            user=user,
        )
        previous_local_file = getattr(work, image_field)
        upload_ids = list(
            ImageUpload.objects.select_for_update().filter(
                portfolio_work=work,
            ).values_list('pk', flat=True)
        )

        setattr(work, upload_field, None)
        _save_image_target(work, upload_field)

        for upload_id in upload_ids:
            ImageUpload.objects.filter(pk=upload_id).update(
                status=ImageUpload.Status.SUPERSEDED,
                portfolio_work=None,
            )
            _schedule_superseded_cleanup(upload_id)

        work.delete()
        _schedule_local_file_deletion(previous_local_file)


def get_image_url(key: str | None) -> str | None:
    if not key:
        return None

    storage = storages['media_s3']
    try:
        return storage.url(
            key,
            expire=settings.IMAGE_DOWNLOAD_URL_TTL_SECONDS,
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageUnavailable() from exc


def get_entity_image_url(
    instance,
    *,
    image_field='image',
    upload_field='image_upload',
    request=None,
) -> str | None:
    upload_id = getattr(instance, f'{upload_field}_id', None)
    if upload_id is not None:
        upload = getattr(instance, upload_field)
        if upload.status == ImageUpload.Status.ATTACHED:
            return get_image_url(upload.final_key)

    local_image = getattr(instance, image_field)
    if not local_image:
        return None

    url = local_image.url
    if request is not None:
        return request.build_absolute_uri(url)
    return url


def get_upload_image_urls(upload: ImageUpload) -> dict:
    if upload.status not in (
        ImageUpload.Status.READY,
        ImageUpload.Status.ATTACHED,
    ):
        return {
            'image_url': None,
            'thumbnail_url': None,
        }
    return {
        'image_url': get_image_url(upload.final_key),
        'thumbnail_url': get_image_url(upload.thumbnail_key),
    }


def delete_image_object(key: str) -> None:
    storages['media_s3'].delete(key)
