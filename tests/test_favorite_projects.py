import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from projects.models import Project
from users.models import FavoriteProject


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ('method', 'path'),
    [
        ('get', '/api/v1/users/me/favorite-projects/'),
        ('post', '/api/v1/users/me/favorite-projects/'),
        ('delete', '/api/v1/users/me/favorite-projects/1/'),
    ],
)
def test_favorite_project_endpoints_require_auth(
    api_client,
    api_request,
    method,
    path,
):
    response = api_request(api_client, method, path)

    assert response.status_code == 401


def test_participant_can_add_project_to_favorites(
    backend_client,
    api_request,
    participant_backend_user,
    project,
):
    response = api_request(
        backend_client,
        'post',
        '/api/v1/users/me/favorite-projects/',
        data={'project_id': project.pk},
    )

    assert response.status_code == 201
    data = response.json()
    assert data['project_id'] == project.pk
    assert data['user_id'] == participant_backend_user.pk


def test_duplicate_favorite_project_does_not_create_duplicate(
    backend_client,
    api_request,
    project,
    favorite_project,
):
    response = api_request(
        backend_client,
        'post',
        '/api/v1/users/me/favorite-projects/',
        data={'project_id': project.pk},
    )

    assert response.status_code in (400, 409)
    assert FavoriteProject.objects.filter(
        user=favorite_project.user,
        project=project,
    ).count() == 1


def test_favorite_list_contains_nested_project_card_with_roles_preview(
    backend_client,
    api_request,
    favorite_project,
    backend_project_role,
    project_role_skill,
):
    response = api_request(
        backend_client,
        'get',
        '/api/v1/users/me/favorite-projects/',
    )

    assert response.status_code == 200
    item = next(item for item in response.json() if item['id'] == favorite_project.pk)
    assert item['project_id'] == favorite_project.project_id
    assert item['project']['id'] == favorite_project.project_id
    assert item['project']['owner_id'] == favorite_project.project.owner_id
    assert item['project']['field_id'] == favorite_project.project.field_id
    assert item['project']['title'] == favorite_project.project.title
    assert item['project']['description'] == favorite_project.project.description
    assert item['project']['problem'] == favorite_project.project.problem
    assert item['project']['status'] == favorite_project.project.status
    assert item['project']['is_favorited'] is True
    assert item['project']['roles_preview'][0]['id'] == backend_project_role.pk
    assert item['project']['roles_preview'][0]['skills'][0]['id'] == (
        project_role_skill.pk
    )


def test_user_sees_only_own_favorites(
    backend_client,
    api_request,
    project,
    favorite_project,
    participant_designer_user,
    another_project,
):
    other_favorite = FavoriteProject.objects.create(
        user=participant_designer_user,
        project=another_project,
    )

    response = api_request(
        backend_client,
        'get',
        '/api/v1/users/me/favorite-projects/',
    )

    assert response.status_code == 200
    ids = {item['id'] for item in response.json()}
    assert favorite_project.pk in ids
    assert other_favorite.pk not in ids


def test_favorite_list_uses_prefetched_project_list_resources(
    backend_client,
    api_request,
    participant_backend_user,
    owner,
    field,
    favorite_project,
):
    for index in range(3):
        project = Project.objects.create(
            owner=owner,
            field=field,
            title=f'Favorite project {index}',
            description='Project description',
            problem='Project problem',
        )
        FavoriteProject.objects.create(
            user=participant_backend_user,
            project=project,
        )

    with CaptureQueriesContext(connection) as captured:
        response = api_request(
            backend_client,
            'get',
            '/api/v1/users/me/favorite-projects/',
        )

    assert response.status_code == 200
    assert len(response.json()) == 4
    assert len(captured) <= 8
    assert all(item['project']['is_favorited'] is True for item in response.json())


def test_delete_favorite_by_project_id(
    backend_client,
    api_request,
    project,
    favorite_project,
):
    response = api_request(
        backend_client,
        'delete',
        f'/api/v1/users/me/favorite-projects/{project.pk}/',
    )

    assert response.status_code == 204
    assert not FavoriteProject.objects.filter(pk=favorite_project.pk).exists()


def test_delete_missing_favorite_returns_error(
    backend_client,
    api_request,
    project,
):
    response = api_request(
        backend_client,
        'delete',
        f'/api/v1/users/me/favorite-projects/{project.pk}/',
    )

    assert response.status_code in (400, 404)


def test_owner_cannot_add_project_to_favorites(
    owner_client,
    api_request,
    project,
):
    response = api_request(
        owner_client,
        'post',
        '/api/v1/users/me/favorite-projects/',
        data={'project_id': project.pk},
    )

    assert response.status_code == 403
