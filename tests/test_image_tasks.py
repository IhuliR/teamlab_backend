from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import call, patch
from uuid import uuid4

import pytest
from botocore.exceptions import (
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)
from celery.exceptions import Retry
from django.db import close_old_connections, connection
from django.db.models import F
from django.db.models.query import FlatValuesListIterable
from django.utils import timezone

from images.constants import (
    MAX_PROCESSING_ATTEMPTS,
    PROCESSING_TIMEOUT_MINUTES,
    RECOVERY_DISPATCH_INTERVAL_MINUTES,
)
from images.models import ImageUpload
from images.tasks import (
    process_uploaded_image,
    recover_queued_images,
    recover_stuck_images,
)


pytestmark = pytest.mark.django_db

SOURCE_BYTES = b'source-image'
WEBP_BYTES = b'processed-webp'
THUMBNAIL_BYTES = b'thumbnail-webp'


@pytest.fixture
def queued_upload(owner):
    upload_id = uuid4()
    return ImageUpload.objects.create(
        id=upload_id,
        owner=owner,
        kind=ImageUpload.Kind.USER_AVATAR,
        status=ImageUpload.Status.QUEUED,
        temporary_key=f'temporary/{upload_id}/image',
        expires_at=timezone.now() + timedelta(minutes=5),
        declared_size=len(SOURCE_BYTES),
        declared_content_type='image/jpeg',
        actual_size=len(SOURCE_BYTES),
        actual_content_type='image/jpeg',
        etag='"source-etag"',
    )


def client_error(status_code):
    return ClientError(
        {
            'Error': {'Code': str(status_code), 'Message': 'S3 error'},
            'ResponseMetadata': {'HTTPStatusCode': status_code},
        },
        'GetObject',
    )


def test_process_uploaded_image_transitions_to_ready_and_saves_both_keys(
    queued_upload,
):
    def download_while_processing(**kwargs):
        queued_upload.refresh_from_db()
        assert queued_upload.status == ImageUpload.Status.PROCESSING
        assert queued_upload.attempts == 1
        assert queued_upload.processing_started_at is not None
        assert queued_upload.next_attempt_at is None
        return SOURCE_BYTES

    def return_requested_key(*, key, image_bytes):
        return key

    with (
        patch(
            'images.tasks.download_image',
            side_effect=download_while_processing,
        ) as download_mock,
        patch(
            'images.tasks.process_image',
            return_value=(WEBP_BYTES, THUMBNAIL_BYTES),
        ) as process_mock,
        patch(
            'images.tasks.save_processed_image',
            side_effect=return_requested_key,
        ) as save_mock,
    ):
        result = process_uploaded_image.run(str(queued_upload.pk))

    queued_upload.refresh_from_db()
    base_key = f'media/{queued_upload.pk}/g0/a1'
    final_key = f'{base_key}/original.webp'
    thumbnail_key = f'{base_key}/thumbnail.webp'

    assert queued_upload.status == ImageUpload.Status.READY
    assert queued_upload.attempts == 1
    assert queued_upload.final_key == final_key
    assert queued_upload.thumbnail_key == thumbnail_key
    assert queued_upload.completed_at is not None
    assert result == {
        'id': str(queued_upload.pk),
        'webp_size': len(WEBP_BYTES),
        'thumbnail_size': len(THUMBNAIL_BYTES),
    }
    download_mock.assert_called_once_with(
        key=queued_upload.temporary_key,
        expected_etag=queued_upload.etag,
        expected_size=queued_upload.actual_size,
        max_size=1024 * 1024,
    )
    process_mock.assert_called_once_with(SOURCE_BYTES)
    assert save_mock.call_args_list == [
        call(key=final_key, image_bytes=WEBP_BYTES),
        call(key=thumbnail_key, image_bytes=THUMBNAIL_BYTES),
    ]


@pytest.mark.parametrize(
    'existing_status',
    (
        ImageUpload.Status.PROCESSING,
        ImageUpload.Status.READY,
        ImageUpload.Status.FAILED,
    ),
)
def test_process_uploaded_image_skips_non_queued_status(
    queued_upload,
    existing_status,
):
    queued_upload.status = existing_status
    queued_upload.save(update_fields=['status'])
    before = ImageUpload.objects.values().get(pk=queued_upload.pk)

    with patch('images.tasks.download_image') as download_mock:
        result = process_uploaded_image.run(str(queued_upload.pk))

    assert result == {
        'id': str(queued_upload.pk),
        'status': existing_status,
        'skipped': True,
    }
    download_mock.assert_not_called()
    assert ImageUpload.objects.values().get(pk=queued_upload.pk) == before


@pytest.mark.parametrize(
    ('request_retries', 'expected_delay'),
    ((0, 2), (2, 8)),
)
def test_temporary_s3_error_schedules_retry_and_sets_next_attempt(
    queued_upload,
    request_retries,
    expected_delay,
):
    queued_upload.attempts = request_retries
    queued_upload.save(update_fields=['attempts'])
    error = EndpointConnectionError(endpoint_url='https://storage.example')
    started_at = timezone.now()

    process_uploaded_image.push_request(retries=request_retries)
    try:
        with (
            patch('images.tasks.download_image', side_effect=error),
            patch.object(
                process_uploaded_image,
                'retry',
                side_effect=Retry(),
            ) as retry_mock,
        ):
            with pytest.raises(Retry):
                process_uploaded_image.run(str(queued_upload.pk))
    finally:
        process_uploaded_image.pop_request()

    queued_upload.refresh_from_db()
    assert queued_upload.status == ImageUpload.Status.QUEUED
    assert queued_upload.attempts == request_retries + 1
    assert queued_upload.next_attempt_at is not None
    retry_mock.assert_called_once()
    assert retry_mock.call_args.kwargs['exc'] is error
    assert retry_mock.call_args.kwargs['countdown'] == expected_delay
    delay = (queued_upload.next_attempt_at - started_at).total_seconds()
    assert expected_delay - 1 <= delay <= expected_delay + 1


def test_temporary_s3_error_on_last_attempt_is_not_retried(queued_upload):
    queued_upload.attempts = MAX_PROCESSING_ATTEMPTS - 1
    queued_upload.save(update_fields=['attempts'])
    error = EndpointConnectionError(endpoint_url='https://storage.example')

    with (
        patch('images.tasks.download_image', side_effect=error),
        patch.object(process_uploaded_image, 'retry') as retry_mock,
    ):
        with pytest.raises(EndpointConnectionError):
            process_uploaded_image.run(str(queued_upload.pk))

    queued_upload.refresh_from_db()
    assert queued_upload.status == ImageUpload.Status.FAILED
    assert queued_upload.attempts == MAX_PROCESSING_ATTEMPTS
    assert queued_upload.error_code == 'storage_error'
    assert queued_upload.next_attempt_at is None
    retry_mock.assert_not_called()


def test_upload_with_exhausted_attempts_fails_without_processing(
    queued_upload,
):
    queued_upload.attempts = MAX_PROCESSING_ATTEMPTS
    queued_upload.next_attempt_at = timezone.now() - timedelta(seconds=1)
    queued_upload.save(update_fields=['attempts', 'next_attempt_at'])

    with patch('images.tasks.download_image') as download_mock:
        result = process_uploaded_image.run(str(queued_upload.pk))

    queued_upload.refresh_from_db()
    assert result['skipped'] is True
    assert queued_upload.status == ImageUpload.Status.FAILED
    assert queued_upload.attempts == MAX_PROCESSING_ATTEMPTS
    assert queued_upload.error_code == 'attempts_exhausted'
    assert queued_upload.next_attempt_at is None
    download_mock.assert_not_called()


@pytest.mark.parametrize(
    'error',
    (
        client_error(403),
        NoCredentialsError(),
    ),
    ids=('client-error-403', 'missing-credentials'),
)
def test_permanent_s3_error_marks_upload_failed(queued_upload, error):
    with (
        patch('images.tasks.download_image', side_effect=error),
        patch.object(process_uploaded_image, 'retry') as retry_mock,
    ):
        with pytest.raises(type(error)):
            process_uploaded_image.run(str(queued_upload.pk))

    queued_upload.refresh_from_db()
    assert queued_upload.status == ImageUpload.Status.FAILED
    assert queued_upload.attempts == 1
    assert queued_upload.error_code == 'storage_error'
    assert queued_upload.next_attempt_at is None
    retry_mock.assert_not_called()


def test_invalid_image_marks_upload_failed(queued_upload):
    with (
        patch('images.tasks.download_image', return_value=SOURCE_BYTES),
        patch(
            'images.tasks.process_image',
            side_effect=ValueError('invalid image'),
        ),
        patch('images.tasks.save_processed_image') as save_mock,
    ):
        with pytest.raises(ValueError, match='invalid image'):
            process_uploaded_image.run(str(queued_upload.pk))

    queued_upload.refresh_from_db()
    assert queued_upload.status == ImageUpload.Status.FAILED
    assert queued_upload.attempts == 1
    assert queued_upload.error_code == 'invalid_image'
    assert queued_upload.error_message
    save_mock.assert_not_called()


def test_process_uploaded_image_skips_premature_delivery(queued_upload):
    next_attempt_at = timezone.now() + timedelta(minutes=1)
    queued_upload.next_attempt_at = next_attempt_at
    queued_upload.save(update_fields=['next_attempt_at'])

    with patch('images.tasks.download_image') as download_mock:
        result = process_uploaded_image.run(str(queued_upload.pk))

    queued_upload.refresh_from_db()
    assert result == {
        'id': str(queued_upload.pk),
        'status': ImageUpload.Status.QUEUED,
        'skipped': True,
        'reason': 'not_due_yet',
    }
    assert queued_upload.status == ImageUpload.Status.QUEUED
    assert queued_upload.attempts == 0
    assert queued_upload.next_attempt_at == next_attempt_at
    download_mock.assert_not_called()


def test_recover_queued_images_limits_publication_frequency(queued_upload):
    with patch('images.tasks.process_uploaded_image.delay') as delay_mock:
        assert recover_queued_images.run() == 1
        assert recover_queued_images.run() == 0

        queued_upload.refresh_from_db()
        queued_upload.last_dispatched_at = timezone.now() - timedelta(
            minutes=RECOVERY_DISPATCH_INTERVAL_MINUTES + 1,
        )
        queued_upload.save(update_fields=['last_dispatched_at'])

        assert recover_queued_images.run() == 1

    assert delay_mock.call_args_list == [
        call(str(queued_upload.pk)),
        call(str(queued_upload.pk)),
    ]


def test_recover_queued_images_releases_reservation_on_publish_error(
    queued_upload,
):
    with patch(
        'images.tasks.process_uploaded_image.delay',
        side_effect=ConnectionError('Redis unavailable'),
    ):
        assert recover_queued_images.run() == 0

    queued_upload.refresh_from_db()
    assert queued_upload.status == ImageUpload.Status.QUEUED
    assert queued_upload.last_dispatched_at is None


@pytest.mark.django_db(transaction=True)
def test_concurrent_recovery_reserves_queued_upload_once(queued_upload):
    assert connection.vendor == 'postgresql'
    selection_barrier = Barrier(2)
    original_iter = FlatValuesListIterable.__iter__

    def synchronize_selected_ids(iterable):
        selected_ids = list(original_iter(iterable))
        selection_barrier.wait(timeout=5)
        yield from selected_ids

    def recover_in_separate_connection():
        close_old_connections()
        try:
            return recover_queued_images.run()
        finally:
            close_old_connections()

    with (
        patch.object(
            FlatValuesListIterable,
            '__iter__',
            synchronize_selected_ids,
        ),
        patch('images.tasks.process_uploaded_image.delay') as delay_mock,
        ThreadPoolExecutor(max_workers=2) as executor,
    ):
        futures = [
            executor.submit(recover_in_separate_connection)
            for _ in range(2)
        ]
        recovered_counts = [future.result(timeout=10) for future in futures]

    queued_upload.refresh_from_db()
    assert sorted(recovered_counts) == [0, 1]
    assert queued_upload.last_dispatched_at is not None
    delay_mock.assert_called_once_with(str(queued_upload.pk))


def test_recover_stuck_images_returns_only_timed_out_processing_to_queue(
    queued_upload,
):
    stuck_started_at = timezone.now() - timedelta(
        minutes=PROCESSING_TIMEOUT_MINUTES + 1,
    )
    queued_upload.status = ImageUpload.Status.PROCESSING
    queued_upload.processing_started_at = stuck_started_at
    queued_upload.attempts = 2
    queued_upload.generation = 3
    queued_upload.save(
        update_fields=[
            'status',
            'processing_started_at',
            'attempts',
            'generation',
        ],
    )

    active_id = uuid4()
    active_upload = ImageUpload.objects.create(
        id=active_id,
        owner=queued_upload.owner,
        kind=ImageUpload.Kind.USER_AVATAR,
        status=ImageUpload.Status.PROCESSING,
        temporary_key=f'temporary/{active_id}/image',
        expires_at=timezone.now() + timedelta(minutes=5),
        declared_size=1,
        declared_content_type='image/jpeg',
        actual_size=1,
        actual_content_type='image/jpeg',
        etag='"active-etag"',
        processing_started_at=timezone.now(),
    )

    before_recovery = timezone.now()
    assert recover_stuck_images.run() == 1

    queued_upload.refresh_from_db()
    active_upload.refresh_from_db()
    assert queued_upload.status == ImageUpload.Status.QUEUED
    assert queued_upload.processing_started_at is None
    assert queued_upload.next_attempt_at >= before_recovery
    assert queued_upload.attempts == 2
    assert queued_upload.generation == 3
    assert active_upload.status == ImageUpload.Status.PROCESSING
    assert active_upload.processing_started_at is not None


@pytest.mark.parametrize('changed_field', ('attempts', 'generation'))
def test_final_update_rejects_stale_worker(queued_upload, changed_field):
    changed = False

    def save_after_state_change(*, key, image_bytes):
        nonlocal changed
        if not changed:
            ImageUpload.objects.filter(pk=queued_upload.pk).update(
                **{changed_field: F(changed_field) + 1},
            )
            changed = True
        return key

    with (
        patch('images.tasks.download_image', return_value=SOURCE_BYTES),
        patch(
            'images.tasks.process_image',
            return_value=(WEBP_BYTES, THUMBNAIL_BYTES),
        ),
        patch(
            'images.tasks.save_processed_image',
            side_effect=save_after_state_change,
        ) as save_mock,
    ):
        with pytest.raises(
            RuntimeError,
            match='Статус загрузки изменился во время обработки',
        ):
            process_uploaded_image.run(str(queued_upload.pk))

    queued_upload.refresh_from_db()
    assert queued_upload.status == ImageUpload.Status.PROCESSING
    assert queued_upload.final_key is None
    assert queued_upload.thumbnail_key is None
    assert save_mock.call_count == 2
