import pytest


pytestmark = pytest.mark.django_db


def assert_paginated_response(data):
    assert set(('count', 'next', 'previous', 'results')).issubset(data)
    assert isinstance(data['count'], int)
    assert isinstance(data['results'], list)


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
    assert data['source'] == 'application'
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

    assert response.status_code == 409
    data = response.json()
    assert 'detail' in data
    assert isinstance(data['detail'], str)


def test_owner_can_invite_participant_to_project_role(
    owner_client,
    api_request,
    project_role,
    participant,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/project-roles/{project_role.pk}/invite/',
        data={'user_id': participant.pk},
    )

    assert response.status_code == 201
    data = response.json()
    assert data['user_id'] == participant.pk
    assert data['project_role_id'] == project_role.pk
    assert data['source'] == 'invitation'
    assert data['status'] == 'pending'


def test_invited_participant_can_accept_invitation(
    owner_client,
    participant_client,
    api_request,
    project_role,
    participant,
):
    invite_response = api_request(
        owner_client,
        'post',
        f'/api/v1/project-roles/{project_role.pk}/invite/',
        data={'user_id': participant.pk},
    )
    assert invite_response.status_code == 201
    interest_id = invite_response.json()['id']

    response = api_request(
        participant_client,
        'post',
        f'/api/v1/role-interests/{interest_id}/accept/',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['user_id'] == participant.pk
    assert data['project_role_id'] == project_role.pk
    assert data['accepted_interest_id'] == interest_id
    assert data['status'] == 'active'


def test_owner_cannot_accept_invitation_for_participant(
    owner_client,
    api_request,
    project_role,
    participant,
):
    invite_response = api_request(
        owner_client,
        'post',
        f'/api/v1/project-roles/{project_role.pk}/invite/',
        data={'user_id': participant.pk},
    )
    assert invite_response.status_code == 201
    interest_id = invite_response.json()['id']

    response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{interest_id}/accept/',
    )

    assert response.status_code == 403
    data = response.json()
    assert 'detail' in data
    assert isinstance(data['detail'], str)


def test_other_participant_cannot_accept_invitation(
    owner_client,
    second_participant_client,
    api_request,
    project_role,
    participant,
):
    invite_response = api_request(
        owner_client,
        'post',
        f'/api/v1/project-roles/{project_role.pk}/invite/',
        data={'user_id': participant.pk},
    )
    assert invite_response.status_code == 201
    interest_id = invite_response.json()['id']

    response = api_request(
        second_participant_client,
        'post',
        f'/api/v1/role-interests/{interest_id}/accept/',
    )

    assert response.status_code == 403
    data = response.json()
    assert 'detail' in data
    assert isinstance(data['detail'], str)


def test_owner_can_reject_role_interest(
    owner_client,
    api_request,
    role_interest,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{role_interest.pk}/reject/',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == role_interest.pk
    assert data['status'] == 'rejected'


def test_my_interests_requires_authentication(api_client, api_request):
    response = api_request(api_client, 'get', '/api/v1/users/me/interests/')

    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert isinstance(data['detail'], str)


def test_my_interests_uses_paginated_response(
    participant_client,
    api_request,
    role_interest,
):
    response = api_request(
        participant_client,
        'get',
        '/api/v1/users/me/interests/',
    )

    assert response.status_code == 200
    data = response.json()
    assert_paginated_response(data)
    assert any(item['id'] == role_interest.pk for item in data['results'])


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
