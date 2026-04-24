import pytest


pytestmark = pytest.mark.django_db


def test_participant_can_create_role_interest(
    participant_client,
    api_request,
    project_role,
    participant,
):
    response = api_request(
        participant_client,
        'post',
        f'/api/v1/project-roles/{project_role.pk}/interests/',
    )

    assert response.status_code == 201
    data = response.json()
    assert data['user_id'] == participant.pk
    assert data['project_role_id'] == project_role.pk
    assert data['status'] == 'pending'


def test_duplicate_role_interest_returns_validation_error(
    participant_client,
    api_request,
    project_role,
    role_interest,
):
    response = api_request(
        participant_client,
        'post',
        f'/api/v1/project-roles/{project_role.pk}/interests/',
    )

    assert response.status_code == 400


def test_closed_role_interest_creation_returns_error(
    participant_client,
    api_request,
    closed_project_role,
):
    response = api_request(
        participant_client,
        'post',
        f'/api/v1/project-roles/{closed_project_role.pk}/interests/',
    )

    assert response.status_code == 400


def test_closed_project_interest_creation_returns_error(
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
