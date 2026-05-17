import pytest


pytestmark = pytest.mark.django_db


def test_owner_can_create_project(
    owner_client,
    api_request,
    project_payload,
):
    response = api_request(
        owner_client,
        'post',
        '/api/v1/projects/',
        data=project_payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data['title'] == project_payload['title']
    assert data['field_id'] == project_payload['field_id']
    assert data['status'] == 'open'


def test_unauthenticated_user_cannot_create_project(
    api_client,
    api_request,
    project_payload,
):
    response = api_request(
        api_client,
        'post',
        '/api/v1/projects/',
        data=project_payload,
    )

    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert isinstance(data['detail'], str)


def test_project_list_uses_paginated_response(
    api_client,
    api_request,
    project,
):
    response = api_request(api_client, 'get', '/api/v1/projects/')

    assert response.status_code == 200
    data = response.json()
    assert set(('count', 'next', 'previous', 'results')).issubset(data)
    assert isinstance(data['count'], int)
    assert isinstance(data['results'], list)
    assert any(item['id'] == project.pk for item in data['results'])


def test_project_not_found_returns_detail_error(api_client, api_request):
    response = api_request(api_client, 'get', '/api/v1/projects/999999/')

    assert response.status_code == 404
    data = response.json()
    assert 'detail' in data
    assert isinstance(data['detail'], str)


def test_closed_project_rejects_new_interest(
    participant_client,
    api_request,
    role_in_closed_project,
):
    response = api_request(
        participant_client,
        'post',
        f'/api/v1/project-roles/{role_in_closed_project.pk}/interests/',
    )

    assert response.status_code == 400
