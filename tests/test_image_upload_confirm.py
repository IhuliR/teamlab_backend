from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from uuid import uuid4
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.db.models.signals import post_save
from django.utils import timezone

from images.models import ImageUpload
from images.services import confirm_image_upload


pytestmark = pytest.mark.django_db

UPLOADED_SIZE = 12_345
UPLOADED_CONTENT_TYPE = 'image/jpeg'
UPLOADED_ETAG = '"image-etag"'
UPLOADED_METADATA = {
    'ContentLength': UPLOADED_SIZE,
    'ContentType': UPLOADED_CONTENT_TYPE,
    'ETag': UPLOADED_ETAG,
}


@pytest.fixture
def image_upload(owner):
    upload_id = uuid4()
    return ImageUpload.objects.create(
        id=upload_id,
        owner=owner,
        kind=ImageUpload.Kind.USER_AVATAR,
        temporary_key=f'temporary/{upload_id}/image',
        declared_size=UPLOADED_SIZE,
        declared_content_type=UPLOADED_CONTENT_TYPE,
        expires_at=timezone.now() + timezone.timedelta(minutes=5),
    )


@pytest.fixture
def uploaded_object_metadata_mock():
    with patch(
        'images.services.get_uploaded_object_metadata',
        return_value=UPLOADED_METADATA,
    ) as mocked:
        yield mocked


def confirm_url(upload_id):
    return f'/api/v1/image-uploads/{upload_id}/confirm/'


def database_state(upload):
    return ImageUpload.objects.values().get(pk=upload.pk)


def test_confirm_image_upload_queues_upload_and_saves_metadata(
    uploaded_object_metadata_mock,
    owner_client,
    api_request,
    image_upload,
):
    response = api_request(
        owner_client,
        'post',
        confirm_url(image_upload.pk),
    )

    assert response.status_code == 200
    assert response.json() == {
        'upload_id': str(image_upload.pk),
        'status': ImageUpload.Status.QUEUED,
    }
    image_upload.refresh_from_db()
    assert image_upload.status == ImageUpload.Status.QUEUED
    assert image_upload.actual_size == UPLOADED_SIZE
    assert image_upload.actual_content_type == UPLOADED_CONTENT_TYPE
    assert image_upload.etag == UPLOADED_ETAG
    uploaded_object_metadata_mock.assert_called_once_with(
        key=image_upload.temporary_key,
    )


def test_confirm_queued_upload_is_idempotent_without_s3_head(
    uploaded_object_metadata_mock,
    owner_client,
    api_request,
    image_upload,
):
    image_upload.status = ImageUpload.Status.QUEUED
    image_upload.actual_size = UPLOADED_SIZE
    image_upload.actual_content_type = UPLOADED_CONTENT_TYPE
    image_upload.etag = UPLOADED_ETAG
    image_upload.save(
        update_fields=[
            'status',
            'actual_size',
            'actual_content_type',
            'etag',
        ],
    )
    before = database_state(image_upload)

    response = api_request(
        owner_client,
        'post',
        confirm_url(image_upload.pk),
    )

    assert response.status_code == 200
    assert response.json()['status'] == ImageUpload.Status.QUEUED
    uploaded_object_metadata_mock.assert_not_called()
    assert database_state(image_upload) == before


def test_confirm_foreign_upload_returns_not_found(
    uploaded_object_metadata_mock,
    backend_client,
    api_request,
    image_upload,
):
    before = database_state(image_upload)

    response = api_request(
        backend_client,
        'post',
        confirm_url(image_upload.pk),
    )

    assert response.status_code == 404
    uploaded_object_metadata_mock.assert_not_called()
    assert database_state(image_upload) == before


def test_confirm_missing_upload_returns_not_found(
    uploaded_object_metadata_mock,
    owner_client,
    api_request,
):
    response = api_request(
        owner_client,
        'post',
        confirm_url(uuid4()),
    )

    assert response.status_code == 404
    uploaded_object_metadata_mock.assert_not_called()


def test_confirm_requires_authentication(
    uploaded_object_metadata_mock,
    api_client,
    api_request,
    image_upload,
):
    before = database_state(image_upload)

    response = api_request(
        api_client,
        'post',
        confirm_url(image_upload.pk),
    )

    assert response.status_code == 401
    uploaded_object_metadata_mock.assert_not_called()
    assert database_state(image_upload) == before


@pytest.mark.parametrize(
    ('status', 'expired'),
    [
        (ImageUpload.Status.AWAITING_UPLOAD, True),
        (ImageUpload.Status.PROCESSING, False),
    ],
    ids=('expired', 'invalid-status'),
)
def test_confirm_rejects_expired_or_invalid_status_without_changes(
    uploaded_object_metadata_mock,
    owner_client,
    api_request,
    image_upload,
    status,
    expired,
):
    image_upload.status = status
    if expired:
        image_upload.expires_at = timezone.now() - timezone.timedelta(seconds=1)
    image_upload.save(update_fields=['status', 'expires_at'])
    before = database_state(image_upload)

    response = api_request(
        owner_client,
        'post',
        confirm_url(image_upload.pk),
    )

    assert response.status_code == 400
    uploaded_object_metadata_mock.assert_not_called()
    assert database_state(image_upload) == before


def test_confirm_returns_bad_request_when_object_is_missing(
    owner_client,
    api_request,
    image_upload,
):
    missing_object_error = ClientError(
        {
            'Error': {
                'Code': 'NoSuchKey',
                'Message': 'Object does not exist',
            },
        },
        'HeadObject',
    )
    before = database_state(image_upload)

    with patch(
        'images.services.get_uploaded_object_metadata',
        side_effect=missing_object_error,
    ) as metadata_mock:
        response = api_request(
            owner_client,
            'post',
            confirm_url(image_upload.pk),
        )

    assert response.status_code == 400
    metadata_mock.assert_called_once_with(key=image_upload.temporary_key)
    assert database_state(image_upload) == before


def test_confirm_returns_service_unavailable_when_s3_is_unavailable(
    owner_client,
    api_request,
    image_upload,
):
    unavailable_error = EndpointConnectionError(
        endpoint_url='https://storage.example.test',
    )
    before = database_state(image_upload)

    with patch(
        'images.services.get_uploaded_object_metadata',
        side_effect=unavailable_error,
    ) as metadata_mock:
        response = api_request(
            owner_client,
            'post',
            confirm_url(image_upload.pk),
        )

    assert response.status_code == 503
    metadata_mock.assert_called_once_with(key=image_upload.temporary_key)
    assert database_state(image_upload) == before


@pytest.mark.parametrize(
    ('declared_size', 'metadata'),
    [
        (
            UPLOADED_SIZE,
            {
                **UPLOADED_METADATA,
                'ContentLength': UPLOADED_SIZE + 1,
            },
        ),
        (
            settings.IMAGE_UPLOAD_LIMITS[ImageUpload.Kind.USER_AVATAR] + 1,
            {
                **UPLOADED_METADATA,
                'ContentLength': (
                    settings.IMAGE_UPLOAD_LIMITS[
                        ImageUpload.Kind.USER_AVATAR
                    ] + 1
                ),
            },
        ),
        (
            UPLOADED_SIZE,
            {
                **UPLOADED_METADATA,
                'ContentType': 'image/png',
            },
        ),
    ],
    ids=('size-mismatch', 'size-limit', 'mime-mismatch'),
)
def test_confirm_rejects_invalid_uploaded_object_metadata(
    owner_client,
    api_request,
    image_upload,
    declared_size,
    metadata,
):
    image_upload.declared_size = declared_size
    image_upload.save(update_fields=['declared_size'])
    before = database_state(image_upload)

    with patch(
        'images.services.get_uploaded_object_metadata',
        return_value=metadata,
    ) as metadata_mock:
        response = api_request(
            owner_client,
            'post',
            confirm_url(image_upload.pk),
        )

    assert response.status_code == 400
    metadata_mock.assert_called_once_with(key=image_upload.temporary_key)
    assert database_state(image_upload) == before


@pytest.mark.django_db(transaction=True)
def test_concurrent_confirms_queue_upload_once(owner, image_upload):
    assert connection.vendor == 'postgresql'
    barrier = Barrier(2)
    transition_lock = Lock()
    transitions = []

    def metadata_after_both_requests_start(*, key):
        assert key == image_upload.temporary_key
        barrier.wait(timeout=5)
        return UPLOADED_METADATA

    def record_transition(sender, instance, created, update_fields, **kwargs):
        if instance.pk != image_upload.pk or created:
            return
        if update_fields and 'status' in update_fields:
            with transition_lock:
                transitions.append(instance.status)

    def confirm_in_separate_connection():
        close_old_connections()
        try:
            user = get_user_model().objects.get(pk=owner.pk)
            return confirm_image_upload(
                user=user,
                upload_id=image_upload.pk,
            ).status
        finally:
            close_old_connections()

    post_save.connect(
        record_transition,
        sender=ImageUpload,
        weak=False,
        dispatch_uid='test_concurrent_image_upload_confirmation',
    )
    try:
        with patch(
            'images.services.get_uploaded_object_metadata',
            side_effect=metadata_after_both_requests_start,
        ) as metadata_mock:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(confirm_in_separate_connection)
                    for _ in range(2)
                ]
                statuses = [future.result(timeout=10) for future in futures]
    finally:
        post_save.disconnect(
            sender=ImageUpload,
            dispatch_uid='test_concurrent_image_upload_confirmation',
        )

    image_upload.refresh_from_db()
    assert statuses == [ImageUpload.Status.QUEUED] * 2
    assert image_upload.status == ImageUpload.Status.QUEUED
    assert image_upload.actual_size == UPLOADED_SIZE
    assert image_upload.actual_content_type == UPLOADED_CONTENT_TYPE
    assert image_upload.etag == UPLOADED_ETAG
    assert transitions == [ImageUpload.Status.QUEUED]
    assert metadata_mock.call_count == 2
