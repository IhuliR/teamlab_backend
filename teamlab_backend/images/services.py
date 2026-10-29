import logging
import uuid
from datetime import timedelta
from functools import partial

import boto3

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
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
            ['content-length-range', 1, max_size],
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
