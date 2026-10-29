import logging
from datetime import timedelta
from uuid import UUID

from botocore.exceptions import (
    BotoCoreError,
    ConnectionClosedError,
    ResponseStreamingError,
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)
from celery import shared_task
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.utils import timezone

from .processing import process_image
from .services import download_image, save_processed_image
from .models import ImageUpload
from .constants import (
    MAX_PROCESSING_ATTEMPTS,
    PROCESSING_TIMEOUT_MINUTES,
    RECOVERY_DISPATCH_INTERVAL_MINUTES,
)


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_uploaded_image(self, upload_id: str) -> dict:
    with transaction.atomic():
        upload = ImageUpload.objects.select_for_update().get(
            pk=UUID(upload_id)
        )

        if upload.status != ImageUpload.Status.QUEUED:
            return {
                'id': str(upload.pk),
                'status': upload.status,
                'skipped': True,
            }

        if (
            upload.next_attempt_at is not None
            and upload.next_attempt_at > timezone.now()
        ):
            return {
                'id': str(upload.pk),
                'status': upload.status,
                'skipped': True,
                'reason': 'not_due_yet',
            }

        if upload.attempts >= MAX_PROCESSING_ATTEMPTS:
            upload.status = ImageUpload.Status.FAILED
            upload.error_code = 'attempts_exhausted'
            upload.error_message = 'Превышено количество попыток обработки.'
            upload.next_attempt_at = None

            upload.save(
                update_fields=[
                    'status',
                    'error_code',
                    'error_message',
                    'next_attempt_at',
                ]
            )

            return {
                'id': str(upload.pk),
                'status': upload.status,
                'skipped': True,
            }

        if upload.etag is None or upload.actual_size is None:
            raise ValueError('Загрузка не подтверждена.')

        max_size = settings.IMAGE_UPLOAD_LIMITS[upload.kind]

        upload.status = ImageUpload.Status.PROCESSING
        upload.processing_started_at = timezone.now()
        upload.attempts += 1
        upload.next_attempt_at = None

        attempts_number = upload.attempts
        generation = upload.generation

        upload.save(
            update_fields=[
                'status',
                'processing_started_at',
                'attempts',
                'next_attempt_at',
            ]
        )

    try:
        image_bytes = download_image(
            key=upload.temporary_key,
            expected_etag=upload.etag,
            expected_size=upload.actual_size,
            max_size=max_size,
        )
        webp_bytes, thumbnail_bytes = process_image(image_bytes)
        base_key = (
            f'media/{upload.id}/'
            f'g{generation}/a{attempts_number}'
        )
        final_key = f'{base_key}/original.webp'
        thumbnail_key = f'{base_key}/thumbnail.webp'
        saved_final_key = save_processed_image(
            key=final_key,
            image_bytes=webp_bytes
        )
        saved_thumbnail_key = save_processed_image(
            key=thumbnail_key,
            image_bytes=thumbnail_bytes
        )

        with transaction.atomic():
            updated = ImageUpload.objects.filter(
                pk=upload.pk,
                status=ImageUpload.Status.PROCESSING,
                attempts=attempts_number,
                generation=generation,
            ).update(
                final_key=saved_final_key,
                thumbnail_key=saved_thumbnail_key,
                status=ImageUpload.Status.READY,
                completed_at=timezone.now(),
                error_code=None,
                error_message='',
            )

            if updated != 1:
                raise RuntimeError(
                    'Статус загрузки изменился во время обработки.'
                )

    except ValueError:
        ImageUpload.objects.filter(
            pk=upload.pk,
            status=ImageUpload.Status.PROCESSING,
            attempts=attempts_number,
            generation=generation,
        ).update(
            status=ImageUpload.Status.FAILED,
            error_code='invalid_image',
            error_message='Не удалось обработать изображение.',
        )
        logging.exception('Некорректное изображение: %s', upload.pk)
        raise

    except (
        ClientError,
        ConnectTimeoutError,
        ConnectionClosedError,
        ResponseStreamingError,
        EndpointConnectionError,
        ReadTimeoutError,
    ) as exc:
        if isinstance(exc, ClientError):
            status_code = exc.response.get(
                'ResponseMetadata', {}
            ).get('HTTPStatusCode')

            is_temporary = status_code in (429, 500, 502, 503, 504)
        else:
            is_temporary = True

        can_retry = (
            is_temporary
            and attempts_number < MAX_PROCESSING_ATTEMPTS
        )

        if can_retry:
            delay = 2 ** (self.request.retries + 1)

            updated = ImageUpload.objects.filter(
                pk=upload.pk,
                status=ImageUpload.Status.PROCESSING,
                attempts=attempts_number,
                generation=generation,
            ).update(
                status=ImageUpload.Status.QUEUED,
                next_attempt_at=timezone.now() + timedelta(seconds=delay)
            )

            if updated == 1:
                logger.warning(
                    'Повторная обработка изображения %s через %s сек.',
                    upload.pk,
                    delay,
                )
                raise self.retry(exc=exc, countdown=delay)

        ImageUpload.objects.filter(
            pk=upload.pk,
            status=ImageUpload.Status.PROCESSING,
            attempts=attempts_number,
            generation=generation,
        ).update(
            status=ImageUpload.Status.FAILED,
            error_code='storage_error',
            error_message='Не удалось получить доступ к хранилищу.',
        )

        logger.exception('Ошибка S3 при обработке %s', upload.pk)
        raise

    except BotoCoreError:
        ImageUpload.objects.filter(
            pk=upload.pk,
            status=ImageUpload.Status.PROCESSING,
            attempts=attempts_number,
            generation=generation,
        ).update(
            status=ImageUpload.Status.FAILED,
            error_code='storage_error',
            error_message='Ошибка доступа к хранилищу.',
            next_attempt_at=None,
        )
        logger.exception(
            'Ошибка boto3 при обработке изображения %s',
            upload.pk,
        )
        raise

    except Exception:
        logger.exception('Ошибка обработки изображения: %s', upload.pk)
        raise

    return {
        'id': str(upload.pk),
        'webp_size': len(webp_bytes),
        'thumbnail_size': len(thumbnail_bytes),
    }


@shared_task
def recover_queued_images() -> int:
    now = timezone.now()
    cutoff = now - timedelta(
        minutes=RECOVERY_DISPATCH_INTERVAL_MINUTES
    )
    conditions = (
        Q(last_dispatched_at__isnull=True)
        | Q(last_dispatched_at__lte=cutoff)
    )

    upload_ids = list(
        ImageUpload.objects.filter(
            conditions,
            status=ImageUpload.Status.QUEUED,
        ).filter(
            Q(next_attempt_at__isnull=True)
            | Q(next_attempt_at__lte=now)
        ).order_by('created_at').values_list('pk', flat=True)[:50]
    )

    recovered = 0

    for upload_id in upload_ids:
        dispatched_at = timezone.now()

        updated = ImageUpload.objects.filter(
            conditions,
            pk=upload_id,
            status=ImageUpload.Status.QUEUED,
        ).filter(
            Q(next_attempt_at__isnull=True)
            | Q(next_attempt_at__lte=dispatched_at)
        ).update(
            last_dispatched_at=dispatched_at,
        )
        if updated != 1:
            continue

        try:
            process_uploaded_image.delay(str(upload_id))
        except Exception:
            ImageUpload.objects.filter(
                pk=upload_id,
                status=ImageUpload.Status.QUEUED,
                last_dispatched_at=dispatched_at,
            ).update(last_dispatched_at=None)

            logger.exception(
                'Не удалось повторно отправить изображение %s',
                upload_id
            )
        else:
            recovered += 1

    return recovered


@shared_task
def recover_stuck_images() -> int:
    cutoff = timezone.now() - timedelta(
        minutes=PROCESSING_TIMEOUT_MINUTES
    )

    upload_ids = list(
        ImageUpload.objects.filter(
            status=ImageUpload.Status.PROCESSING,
            processing_started_at__lte=cutoff,
        ).values_list('pk', flat=True)[:50]
    )
    recovered = 0

    for upload_id in upload_ids:
        updated = ImageUpload.objects.filter(
            pk=upload_id,
            status=ImageUpload.Status.PROCESSING,
            processing_started_at__lte=cutoff,
        ).update(
            status=ImageUpload.Status.QUEUED,
            processing_started_at=None,
            next_attempt_at=timezone.now(),
        )

        recovered += updated

    return recovered
