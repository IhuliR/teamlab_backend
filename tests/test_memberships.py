import pytest


pytestmark = pytest.mark.django_db


def test_accept_interest_creates_project_membership(
    owner_client,
    api_request,
    project,
    role_interest,
):
    accept_response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{role_interest.pk}/accept/',
    )

    assert accept_response.status_code == 200
    membership_data = accept_response.json()
    assert membership_data['user_id'] == role_interest.user_id
    assert membership_data['project_role_id'] == role_interest.project_role_id
    assert membership_data['accepted_interest_id'] == role_interest.pk

    list_response = api_request(
        owner_client,
        'get',
        '/api/v1/project-memberships/',
        data={'project_id': project.pk},
    )

    assert list_response.status_code == 200
    memberships = list_response.json()
    assert any(
        item['accepted_interest_id'] == role_interest.pk
        and item['user_id'] == role_interest.user_id
        and item['project_role_id'] == role_interest.project_role_id
        for item in memberships
    )


def test_project_membership_cannot_be_created_directly(
    owner_client,
    api_request,
    project,
    project_role,
    participant,
    role_interest,
):
    payload = {
        'user_id': participant.pk,
        'project_role_id': project_role.pk,
        'accepted_interest_id': role_interest.pk,
        'status': 'active',
    }

    response = api_request(
        owner_client,
        'post',
        '/api/v1/project-memberships/',
        data=payload,
    )

    assert response.status_code == 405


def test_accept_interest_respects_role_capacity(
    owner_client,
    api_request,
    project_role,
    role_interest,
    second_participant,
):
    role_interest_model = role_interest.__class__
    second_interest = role_interest_model.objects.create(
        user=second_participant,
        project_role=project_role,
        source='application',
        status='pending',
    )

    first_accept_response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{role_interest.pk}/accept/',
    )
    assert first_accept_response.status_code == 200

    second_accept_response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{second_interest.pk}/accept/',
    )

    assert second_accept_response.status_code == 409
