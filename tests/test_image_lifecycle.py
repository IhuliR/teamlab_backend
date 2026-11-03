from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import call, patch
from uuid import uuid4

import pytest
from celery.exceptions import Retry
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from images.models import ImageUpload
from images.services import attach_image_upload
from images.tasks import (
    cleanup_superseded_images,
    delete_superseded_image,
    process_uploaded_image,
)
from users.models import PortfolioWork


pytestmark = pytest.mark.django_db


@pytest.fixture
def ready_upload_factory(owner):
    def _create(*, kind=ImageUpload.Kind.USER_AVATAR, target=None, user=None):
        upload_id = uuid4()
        target_fields = {}
        if kind == ImageUpload.Kind.PROJECT_IMAGE:
            target_fields['project'] = target
        elif kind == ImageUpload.Kind.PORTFOLIO_IMAGE:
            target_fields['portfolio_work'] = target

        return ImageUpload.objects.create(
            id=upload_id,
            owner=user or owner,
            kind=kind,
            status=ImageUpload.Status.READY,
            temporary_key=f'temporary/{upload_id}/image',
            expires_at=timezone.now() + timedelta(minutes=5),
            declared_size=100,
            declared_content_type='image/jpeg',
            actual_size=100,
            actual_content_type='image/jpeg',
            etag='"etag"',
            final_key=f'media/{upload_id}/original.webp',
            thumbnail_key=f'media/{upload_id}/thumbnail.webp',
            **target_fields,
        )

    return _create


def attach_url(upload):
    return f'/api/v1/image-uploads/{upload.pk}/attach/'


def test_full_mocked_image_lifecycle_chain(
    owner,
    owner_client,
    api_request,
    django_capture_on_commit_callbacks,
):
    source = b'source-image'
    presigned = {
        'url': 'https://storage.example/upload',
        'fields': {'key': 'temporary/image'},
    }
    metadata = {
        'ContentLength': len(source),
        'ContentType': 'image/jpeg',
        'ETag': '"etag"',
    }

    with patch(
        'images.services.generate_upload_url',
        return_value=presigned,
    ):
        created = api_request(
            owner_client,
            'post',
            '/api/v1/image-uploads/',
            data={
                'kind': ImageUpload.Kind.USER_AVATAR,
                'content_type': 'image/jpeg',
                'size_bytes': len(source),
            },
        )

    assert created.status_code == 201
    upload = ImageUpload.objects.get(pk=created.json()['upload_id'])

    with (
        patch(
            'images.services.get_uploaded_object_metadata',
            return_value=metadata,
        ),
        patch('images.tasks.process_uploaded_image.delay') as process_delay,
        django_capture_on_commit_callbacks(execute=True),
    ):
        confirmed = api_request(
            owner_client,
            'post',
            f'/api/v1/image-uploads/{upload.pk}/confirm/',
        )

    assert confirmed.status_code == 200
    assert confirmed.json()['status'] == ImageUpload.Status.QUEUED
    process_delay.assert_called_once_with(str(upload.pk))

    with (
        patch('images.tasks.download_image', return_value=source),
        patch('images.tasks.process_image', return_value=(b'webp', b'thumb')),
        patch(
            'images.tasks.save_processed_image',
            side_effect=lambda *, key, image_bytes: key,
        ),
        patch('images.tasks.delete_image_object') as temporary_delete,
    ):
        process_uploaded_image.run(str(upload.pk))

    upload.refresh_from_db()
    assert upload.status == ImageUpload.Status.READY
    temporary_delete.assert_called_once_with(upload.temporary_key)

    with patch(
        'images.serializers.get_image_url',
        side_effect=lambda key: f'https://signed.example/{key}',
    ):
        attached = api_request(owner_client, 'post', attach_url(upload))

    assert attached.status_code == 200
    assert attached.json()['status'] == ImageUpload.Status.ATTACHED
    owner.refresh_from_db()
    assert owner.avatar_upload_id == upload.pk

    assert api_request(
        owner_client,
        'delete',
        '/api/v1/users/me/avatar/',
    ).status_code == 204
    upload.refresh_from_db()
    assert upload.status == ImageUpload.Status.SUPERSEDED

    with patch('images.tasks.delete_image_object') as delete_object:
        result = delete_superseded_image.run(str(upload.pk))

    assert result == {'deleted': True}
    assert delete_object.call_count == 2
    upload.refresh_from_db()
    assert upload.final_key is None
    assert upload.thumbnail_key is None


def test_avatar_attach_polling_and_idempotency(
    owner,
    owner_client,
    backend_client,
    api_request,
    ready_upload_factory,
):
    upload = ready_upload_factory()

    with patch(
        'images.serializers.get_image_url',
        side_effect=lambda key: f'https://signed.example/{key}',
    ):
        response = api_request(owner_client, 'post', attach_url(upload))
        repeated = api_request(owner_client, 'post', attach_url(upload))
        polling = api_request(
            owner_client,
            'get',
            f'/api/v1/image-uploads/{upload.pk}/',
        )

    assert response.status_code == 200
    assert repeated.status_code == 200
    assert polling.status_code == 200
    assert response.json()['upload_id'] == str(upload.pk)
    assert response.json()['status'] == ImageUpload.Status.ATTACHED
    assert response.json()['image_url'].endswith(upload.final_key)
    assert polling.json()['thumbnail_url'].endswith(upload.thumbnail_key)

    owner.refresh_from_db()
    upload.refresh_from_db()
    assert owner.avatar_upload_id == upload.pk
    assert not owner.avatar
    assert upload.status == ImageUpload.Status.ATTACHED

    foreign = api_request(backend_client, 'post', attach_url(upload))
    foreign_polling = api_request(
        backend_client,
        'get',
        f'/api/v1/image-uploads/{upload.pk}/',
    )
    assert foreign.status_code == 404
    assert foreign_polling.status_code == 404


def test_project_attach_rechecks_current_owner(
    owner,
    owner_client,
    create_user,
    project,
    api_request,
    ready_upload_factory,
):
    upload = ready_upload_factory(
        kind=ImageUpload.Kind.PROJECT_IMAGE,
        target=project,
    )
    project.owner = create_user(account_type='owner', specialization=None)
    project.save(update_fields=['owner'])

    response = api_request(owner_client, 'post', attach_url(upload))

    assert response.status_code == 403
    upload.refresh_from_db()
    project.refresh_from_db()
    assert upload.status == ImageUpload.Status.READY
    assert project.image_upload_id is None


def test_replace_supersedes_previous_upload_after_commit(
    owner,
    owner_client,
    api_request,
    ready_upload_factory,
    django_capture_on_commit_callbacks,
):
    first = ready_upload_factory()
    second = ready_upload_factory()

    with (
        patch('images.serializers.get_image_url', return_value='signed-url'),
        patch('images.tasks.delete_superseded_image.delay') as delete_delay,
        django_capture_on_commit_callbacks(execute=True),
    ):
        assert api_request(
            owner_client,
            'post',
            attach_url(first),
        ).status_code == 200
        assert api_request(
            owner_client,
            'post',
            attach_url(second),
        ).status_code == 200

    first.refresh_from_db()
    second.refresh_from_db()
    owner.refresh_from_db()
    assert first.status == ImageUpload.Status.SUPERSEDED
    assert second.status == ImageUpload.Status.ATTACHED
    assert owner.avatar_upload_id == second.pk
    delete_delay.assert_called_once_with(str(first.pk))


@pytest.mark.parametrize('invalid_status', [
    ImageUpload.Status.AWAITING_UPLOAD,
    ImageUpload.Status.PROCESSING,
    ImageUpload.Status.FAILED,
    ImageUpload.Status.SUPERSEDED,
])
def test_attach_rejects_upload_that_is_not_ready(
    owner_client,
    api_request,
    ready_upload_factory,
    invalid_status,
):
    upload = ready_upload_factory()
    upload.status = invalid_status
    upload.save(update_fields=['status'])

    response = api_request(owner_client, 'post', attach_url(upload))

    assert response.status_code == 400
    upload.refresh_from_db()
    assert upload.status == invalid_status


def test_detach_endpoints_clear_only_owned_images(
    owner,
    owner_client,
    backend_client,
    participant_backend_user,
    project,
    portfolio_work,
    api_request,
    ready_upload_factory,
):
    avatar = ready_upload_factory()
    project_image = ready_upload_factory(
        kind=ImageUpload.Kind.PROJECT_IMAGE,
        target=project,
    )
    portfolio_image = ready_upload_factory(
        kind=ImageUpload.Kind.PORTFOLIO_IMAGE,
        target=portfolio_work,
        user=participant_backend_user,
    )
    attach_image_upload(user=owner, upload_id=avatar.pk)
    attach_image_upload(user=owner, upload_id=project_image.pk)
    attach_image_upload(
        user=participant_backend_user,
        upload_id=portfolio_image.pk,
    )

    assert api_request(
        backend_client,
        'delete',
        f'/api/v1/projects/{project.pk}/image/',
    ).status_code == 403
    assert api_request(
        owner_client,
        'delete',
        '/api/v1/users/me/avatar/',
    ).status_code == 204
    assert api_request(
        owner_client,
        'delete',
        f'/api/v1/projects/{project.pk}/image/',
    ).status_code == 204
    assert api_request(
        backend_client,
        'delete',
        f'/api/v1/users/me/portfolio-works/{portfolio_work.pk}/image/',
    ).status_code == 204

    owner.refresh_from_db()
    project.refresh_from_db()
    portfolio_work.refresh_from_db()
    assert owner.avatar_upload_id is None
    assert project.image_upload_id is None
    assert portfolio_work.image_upload_id is None
    for upload in (avatar, project_image, portfolio_image):
        upload.refresh_from_db()
        assert upload.status == ImageUpload.Status.SUPERSEDED


def test_base64_avatar_replacement_preserves_old_endpoint(
    owner,
    owner_client,
    api_request,
    base64_image,
    ready_upload_factory,
):
    upload = ready_upload_factory()
    attach_image_upload(user=owner, upload_id=upload.pk)

    response = api_request(
        owner_client,
        'put',
        '/api/v1/users/me/avatar/',
        data={'avatar': base64_image},
    )

    assert response.status_code == 200
    assert response.json()['avatar']
    owner.refresh_from_db()
    upload.refresh_from_db()
    assert owner.avatar_upload_id is None
    assert owner.avatar
    assert upload.status == ImageUpload.Status.SUPERSEDED


def test_base64_project_replacement_preserves_patch_contract(
    owner,
    owner_client,
    project,
    api_request,
    base64_image,
    ready_upload_factory,
):
    upload = ready_upload_factory(
        kind=ImageUpload.Kind.PROJECT_IMAGE,
        target=project,
    )
    attach_image_upload(user=owner, upload_id=upload.pk)

    response = api_request(
        owner_client,
        'patch',
        f'/api/v1/projects/{project.pk}/',
        data={'image': base64_image},
    )

    assert response.status_code == 200
    assert response.json()['image']
    project.refresh_from_db()
    upload.refresh_from_db()
    assert project.image_upload_id is None
    assert project.image
    assert upload.status == ImageUpload.Status.SUPERSEDED


def test_base64_portfolio_replacement_preserves_patch_contract(
    participant_backend_user,
    backend_client,
    portfolio_work,
    api_request,
    base64_image,
    ready_upload_factory,
):
    upload = ready_upload_factory(
        kind=ImageUpload.Kind.PORTFOLIO_IMAGE,
        target=portfolio_work,
        user=participant_backend_user,
    )
    attach_image_upload(
        user=participant_backend_user,
        upload_id=upload.pk,
    )

    response = api_request(
        backend_client,
        'patch',
        f'/api/v1/users/me/portfolio-works/{portfolio_work.pk}/',
        data={'image': base64_image},
    )

    assert response.status_code == 200
    assert response.json()['image']
    portfolio_work.refresh_from_db()
    upload.refresh_from_db()
    assert portfolio_work.image_upload_id is None
    assert portfolio_work.image
    assert upload.status == ImageUpload.Status.SUPERSEDED


def test_current_profile_does_not_lazy_load_each_image_upload(
    participant_backend_user,
    backend_client,
    portfolio_work,
    api_request,
    ready_upload_factory,
):
    avatar = ready_upload_factory(user=participant_backend_user)
    portfolio_image = ready_upload_factory(
        kind=ImageUpload.Kind.PORTFOLIO_IMAGE,
        target=portfolio_work,
        user=participant_backend_user,
    )
    attach_image_upload(
        user=participant_backend_user,
        upload_id=avatar.pk,
    )
    attach_image_upload(
        user=participant_backend_user,
        upload_id=portfolio_image.pk,
    )

    with (
        patch('images.services.get_image_url', return_value='signed-url'),
        CaptureQueriesContext(connection) as queries,
    ):
        response = api_request(backend_client, 'get', '/api/v1/users/me/')

    assert response.status_code == 200
    assert response.json()['avatar'] == 'signed-url'
    assert response.json()['portfolio_works'][0]['image'] == 'signed-url'
    direct_upload_queries = [
        query['sql']
        for query in queries
        if 'FROM "images_imageupload"' in query['sql']
    ]
    assert direct_upload_queries == []


def test_deleting_portfolio_work_keeps_cleanup_record(
    participant_backend_user,
    backend_client,
    portfolio_work,
    api_request,
    ready_upload_factory,
):
    upload = ready_upload_factory(
        kind=ImageUpload.Kind.PORTFOLIO_IMAGE,
        target=portfolio_work,
        user=participant_backend_user,
    )
    attach_image_upload(
        user=participant_backend_user,
        upload_id=upload.pk,
    )

    response = api_request(
        backend_client,
        'delete',
        f'/api/v1/users/me/portfolio-works/{portfolio_work.pk}/',
    )

    assert response.status_code == 204
    assert not PortfolioWork.objects.filter(pk=portfolio_work.pk).exists()
    upload.refresh_from_db()
    assert upload.status == ImageUpload.Status.SUPERSEDED
    assert upload.portfolio_work_id is None


def test_superseded_cleanup_deletes_both_objects_and_clears_keys(
    ready_upload_factory,
):
    upload = ready_upload_factory()
    upload.status = ImageUpload.Status.SUPERSEDED
    upload.save(update_fields=['status'])
    final_key = upload.final_key
    thumbnail_key = upload.thumbnail_key

    with patch('images.tasks.delete_image_object') as delete_object:
        result = delete_superseded_image.run(str(upload.pk))

    assert result == {'deleted': True}
    assert delete_object.call_args_list == [
        call(final_key),
        call(thumbnail_key),
    ]
    upload.refresh_from_db()
    assert upload.final_key is None
    assert upload.thumbnail_key is None


def test_cleanup_never_deletes_referenced_upload(
    owner,
    ready_upload_factory,
):
    upload = ready_upload_factory()
    owner.avatar_upload = upload
    owner.save(update_fields=['avatar_upload'])
    upload.status = ImageUpload.Status.SUPERSEDED
    upload.save(update_fields=['status'])

    with patch('images.tasks.delete_image_object') as delete_object:
        result = delete_superseded_image.run(str(upload.pk))

    assert result == {'deleted': False, 'reason': 'still_attached'}
    delete_object.assert_not_called()


def test_cleanup_retries_transient_storage_error(ready_upload_factory):
    upload = ready_upload_factory()
    upload.status = ImageUpload.Status.SUPERSEDED
    upload.save(update_fields=['status'])
    error = ConnectionError('S3 unavailable')

    delete_superseded_image.push_request(retries=0)
    try:
        with (
            patch('images.tasks.delete_image_object', side_effect=error),
            patch.object(
                delete_superseded_image,
                'retry',
                side_effect=Retry(),
            ) as retry_mock,
        ):
            with pytest.raises(Retry):
                delete_superseded_image.run(str(upload.pk))
    finally:
        delete_superseded_image.pop_request()

    retry_mock.assert_called_once_with(exc=error, countdown=2)
    upload.refresh_from_db()
    assert upload.final_key
    assert upload.thumbnail_key


def test_beat_recovers_superseded_cleanup(ready_upload_factory):
    upload = ready_upload_factory()
    upload.status = ImageUpload.Status.SUPERSEDED
    upload.save(update_fields=['status'])

    with patch('images.tasks.delete_superseded_image.delay') as delay_mock:
        assert cleanup_superseded_images.run() == 1

    delay_mock.assert_called_once_with(str(upload.pk))


@pytest.mark.django_db(transaction=True)
def test_concurrent_avatar_attach_serializes_replacement(
    owner,
    ready_upload_factory,
):
    assert connection.vendor == 'postgresql'
    first = ready_upload_factory()
    second = ready_upload_factory()

    def attach(upload_id):
        close_old_connections()
        try:
            user = get_user_model().objects.get(pk=owner.pk)
            return attach_image_upload(user=user, upload_id=upload_id).status
        finally:
            close_old_connections()

    with (
        patch('images.services.dispatch_superseded_cleanup'),
        ThreadPoolExecutor(max_workers=2) as executor,
    ):
        statuses = list(executor.map(attach, (first.pk, second.pk)))

    owner.refresh_from_db()
    first.refresh_from_db()
    second.refresh_from_db()
    assert statuses == [ImageUpload.Status.ATTACHED] * 2
    assert owner.avatar_upload_id in {first.pk, second.pk}
    assert sorted([first.status, second.status]) == sorted([
        ImageUpload.Status.ATTACHED,
        ImageUpload.Status.SUPERSEDED,
    ])
