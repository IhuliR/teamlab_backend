from datetime import datetime
from unittest.mock import patch
from uuid import UUID

import pytest
from django.conf import settings

from images.models import ImageUpload


pytestmark = pytest.mark.django_db

IMAGE_UPLOADS_URL = '/api/v1/image-uploads/'
PRESIGNED_UPLOAD = {
    'url': 'https://storage.example.test/upload',
    'fields': {
        'key': 'temporary/upload/image',
        'policy': 'signed-policy',
    },
}


@pytest.fixture
def generate_upload_url_mock():
    with patch(
        'images.services.generate_upload_url',
        return_value=PRESIGNED_UPLOAD,
    ) as mocked:
        yield mocked


@pytest.fixture
def avatar_upload_payload():
    return {
        'kind': ImageUpload.Kind.USER_AVATAR,
        'content_type': 'image/jpeg',
        'size_bytes': 12_345,
    }


def test_authenticated_user_can_create_avatar_upload_session(
    generate_upload_url_mock,
    owner_client,
    api_request,
    avatar_upload_payload,
    owner,
):
    response = api_request(
        owner_client,
        'post',
        IMAGE_UPLOADS_URL,
        data=avatar_upload_payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert set(data) == {
        'upload_id',
        'status',
        'expires_at',
        'upload_url',
        'upload_fields',
    }
    UUID(data['upload_id'])
    datetime.fromisoformat(data['expires_at'])
    assert data['status'] == ImageUpload.Status.AWAITING_UPLOAD
    assert data['upload_url'] == PRESIGNED_UPLOAD['url']
    assert data['upload_fields'] == PRESIGNED_UPLOAD['fields']

    upload = ImageUpload.objects.get(pk=data['upload_id'])
    assert upload.owner == owner
    assert upload.kind == ImageUpload.Kind.USER_AVATAR
    assert upload.project is None
    assert upload.portfolio_work is None
    assert upload.temporary_key == f'temporary/{upload.id}/image'
    assert upload.declared_size == avatar_upload_payload['size_bytes']
    assert upload.declared_content_type == avatar_upload_payload['content_type']
    assert upload.status == ImageUpload.Status.AWAITING_UPLOAD
    assert upload.expires_at.isoformat() == data['expires_at']
    generate_upload_url_mock.assert_called_once_with(
        key=upload.temporary_key,
        content_type=avatar_upload_payload['content_type'],
        max_size=settings.IMAGE_UPLOAD_LIMITS[ImageUpload.Kind.USER_AVATAR],
    )


def test_image_upload_endpoint_requires_authentication(
    generate_upload_url_mock,
    api_client,
    api_request,
    avatar_upload_payload,
):
    response = api_request(
        api_client,
        'post',
        IMAGE_UPLOADS_URL,
        data=avatar_upload_payload,
    )

    assert response.status_code == 401
    generate_upload_url_mock.assert_not_called()
    assert ImageUpload.objects.count() == 0


@pytest.mark.parametrize(
    'invalid_fields',
    [
        {'content_type': 'image/gif'},
        {
            'size_bytes': (
                settings.IMAGE_UPLOAD_LIMITS[ImageUpload.Kind.USER_AVATAR] + 1
            ),
        },
        {'target_id': 1},
    ],
    ids=('unsupported-mime', 'size-limit', 'avatar-target-id'),
)
def test_invalid_image_upload_payload_returns_bad_request(
    generate_upload_url_mock,
    owner_client,
    api_request,
    avatar_upload_payload,
    invalid_fields,
):
    payload = {**avatar_upload_payload, **invalid_fields}

    response = api_request(
        owner_client,
        'post',
        IMAGE_UPLOADS_URL,
        data=payload,
    )

    assert response.status_code == 400
    generate_upload_url_mock.assert_not_called()
    assert ImageUpload.objects.count() == 0


def test_foreign_project_image_upload_is_forbidden(
    generate_upload_url_mock,
    backend_client,
    api_request,
    project,
):
    response = api_request(
        backend_client,
        'post',
        IMAGE_UPLOADS_URL,
        data={
            'kind': ImageUpload.Kind.PROJECT_IMAGE,
            'target_id': project.pk,
            'content_type': 'image/png',
            'size_bytes': 12_345,
        },
    )

    assert response.status_code == 403
    generate_upload_url_mock.assert_not_called()
    assert ImageUpload.objects.count() == 0
