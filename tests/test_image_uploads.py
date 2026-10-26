from unittest.mock import patch

import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from images.models import ImageUpload
from images.services import create_image_upload


PRESIGNED_UPLOAD = {
    'url': 'https://storage.example.test',
    'fields': {'key': 'temporary/key/image'},
}


@pytest.fixture
def generate_upload_url_mock():
    with patch(
        'images.services.generate_upload_url',
        return_value=PRESIGNED_UPLOAD,
    ) as mocked:
        yield mocked


def upload_data(kind, target_id=None):
    data = {
        'kind': kind,
        'content_type': 'image/jpeg',
        'size_bytes': 12_345,
    }
    if target_id is not None:
        data['target_id'] = target_id
    return data


def assert_upload(
    upload,
    *,
    owner,
    kind,
    project=None,
    portfolio_work=None,
    created_before,
):
    assert upload.owner == owner
    assert upload.kind == kind
    assert upload.project == project
    assert upload.portfolio_work == portfolio_work
    assert upload.temporary_key == f'temporary/{upload.id}/image'
    assert upload.declared_size == 12_345
    assert upload.declared_content_type == 'image/jpeg'
    assert upload.status == ImageUpload.Status.AWAITING_UPLOAD
    assert (upload.expires_at - created_before).total_seconds() == pytest.approx(
        settings.IMAGE_PRESIGN_TTL_SECONDS,
        abs=1,
    )


@pytest.mark.django_db
def test_create_avatar_upload_for_current_user(generate_upload_url_mock, owner):
    created_before = timezone.now()

    upload, presigned = create_image_upload(
        user=owner,
        validated_data=upload_data(ImageUpload.Kind.USER_AVATAR),
    )

    assert presigned == PRESIGNED_UPLOAD
    assert_upload(
        upload,
        owner=owner,
        kind=ImageUpload.Kind.USER_AVATAR,
        created_before=created_before,
    )
    generate_upload_url_mock.assert_called_once_with(
        key=upload.temporary_key,
        content_type='image/jpeg',
        max_size=settings.IMAGE_UPLOAD_LIMITS[ImageUpload.Kind.USER_AVATAR],
    )


@pytest.mark.django_db
def test_project_owner_can_create_image_upload(
    generate_upload_url_mock,
    owner,
    project,
):
    created_before = timezone.now()

    upload, _ = create_image_upload(
        user=owner,
        validated_data=upload_data(
            ImageUpload.Kind.PROJECT_IMAGE,
            target_id=project.pk,
        ),
    )

    assert_upload(
        upload,
        owner=owner,
        kind=ImageUpload.Kind.PROJECT_IMAGE,
        project=project,
        created_before=created_before,
    )


@pytest.mark.django_db
def test_foreign_user_cannot_create_project_image_upload(
    generate_upload_url_mock,
    participant_backend_user,
    project,
):
    with pytest.raises(PermissionDenied):
        create_image_upload(
            user=participant_backend_user,
            validated_data=upload_data(
                ImageUpload.Kind.PROJECT_IMAGE,
                target_id=project.pk,
            ),
        )

    generate_upload_url_mock.assert_not_called()
    assert ImageUpload.objects.count() == 0


@pytest.mark.django_db
def test_portfolio_work_owner_can_create_image_upload(
    generate_upload_url_mock,
    participant_backend_user,
    portfolio_work,
):
    created_before = timezone.now()

    upload, _ = create_image_upload(
        user=participant_backend_user,
        validated_data=upload_data(
            ImageUpload.Kind.PORTFOLIO_IMAGE,
            target_id=portfolio_work.pk,
        ),
    )

    assert_upload(
        upload,
        owner=participant_backend_user,
        kind=ImageUpload.Kind.PORTFOLIO_IMAGE,
        portfolio_work=portfolio_work,
        created_before=created_before,
    )


@pytest.mark.django_db
def test_foreign_user_cannot_create_portfolio_image_upload(
    generate_upload_url_mock,
    owner,
    portfolio_work,
):
    with pytest.raises(PermissionDenied):
        create_image_upload(
            user=owner,
            validated_data=upload_data(
                ImageUpload.Kind.PORTFOLIO_IMAGE,
                target_id=portfolio_work.pk,
            ),
        )

    generate_upload_url_mock.assert_not_called()
    assert ImageUpload.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('kind', 'target_id'),
    [
        (ImageUpload.Kind.PROJECT_IMAGE, 999_999),
        (ImageUpload.Kind.PORTFOLIO_IMAGE, 999_999),
    ],
)
def test_create_image_upload_for_missing_target_raises_not_found(
    generate_upload_url_mock,
    owner,
    kind,
    target_id,
):
    with pytest.raises(NotFound):
        create_image_upload(
            user=owner,
            validated_data=upload_data(kind, target_id=target_id),
        )

    generate_upload_url_mock.assert_not_called()
    assert ImageUpload.objects.count() == 0
