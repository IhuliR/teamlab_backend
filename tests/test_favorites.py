import pytest


pytestmark = pytest.mark.django_db


def test_participant_can_add_project_to_favorites(
    participant_client,
    api_request,
    project,
):
    payload = {'project_id': project.pk}

    response = api_request(
        participant_client,
        'post',
        '/api/v1/users/me/favorite-projects/',
        data=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data['project_id'] == project.pk


def test_duplicate_favorite_project_returns_validation_error(
    participant_client,
    api_request,
    project,
):
    payload = {'project_id': project.pk}
    first_response = api_request(
        participant_client,
        'post',
        '/api/v1/users/me/favorite-projects/',
        data=payload,
    )
    assert first_response.status_code == 201

    second_response = api_request(
        participant_client,
        'post',
        '/api/v1/users/me/favorite-projects/',
        data=payload,
    )

    assert second_response.status_code == 400


def test_owner_can_add_candidate_to_favorites(
    owner_client,
    api_request,
    participant,
):
    payload = {'candidate_id': participant.pk}

    response = api_request(
        owner_client,
        'post',
        '/api/v1/users/me/favorite-candidates/',
        data=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data['candidate_id'] == participant.pk


def test_duplicate_favorite_candidate_returns_validation_error(
    owner_client,
    api_request,
    participant,
):
    payload = {'candidate_id': participant.pk}
    first_response = api_request(
        owner_client,
        'post',
        '/api/v1/users/me/favorite-candidates/',
        data=payload,
    )
    assert first_response.status_code == 201

    second_response = api_request(
        owner_client,
        'post',
        '/api/v1/users/me/favorite-candidates/',
        data=payload,
    )

    assert second_response.status_code == 400
