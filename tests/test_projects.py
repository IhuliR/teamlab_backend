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


def test_participant_cannot_create_project(
    participant_client,
    api_request,
    project_payload,
):
    response = api_request(
        participant_client,
        'post',
        '/api/v1/projects/',
        data=project_payload,
    )

    assert response.status_code == 403


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
