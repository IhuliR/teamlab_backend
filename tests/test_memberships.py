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
        (
            f'/api/v1/project-roles/{role_interest.project_role_id}/'
            f'interests/{role_interest.user_id}/accept/'
        ),
    )

    assert accept_response.status_code == 200
    membership_data = accept_response.json()
    assert membership_data['user_id'] == role_interest.user_id
    assert membership_data['project_role_id'] == role_interest.project_role_id
    assert membership_data['accepted_interest_id'] == role_interest.pk

    list_response = api_request(
        owner_client,
        'get',
        f'/api/v1/projects/{project.pk}/memberships/',
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
        f'/api/v1/projects/{project.pk}/memberships/',
        data=payload,
    )

    assert response.status_code in {403, 405}


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
        status='pending',
    )

    first_accept_response = api_request(
        owner_client,
        'post',
        (
            f'/api/v1/project-roles/{role_interest.project_role_id}/'
            f'interests/{role_interest.user_id}/accept/'
        ),
    )
    assert first_accept_response.status_code == 200

    second_accept_response = api_request(
        owner_client,
        'post',
        (
            f'/api/v1/project-roles/{second_interest.project_role_id}/'
            f'interests/{second_interest.user_id}/accept/'
        ),
    )

    assert second_accept_response.status_code == 400
