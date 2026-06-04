import pytest

from projects.models import ProjectMembership, RoleInterest
from users.models import UserSkill

from .utils import results


pytestmark = pytest.mark.django_db


def test_user_list_is_public_without_private_fields(
    api_client,
    api_request,
    participant_backend_user,
):
    response = api_request(api_client, 'get', '/api/v1/users/')

    assert response.status_code == 200
    item = next(
        item for item in results(response.json())
        if item['id'] == participant_backend_user.pk
    )
    assert 'email' not in item
    assert 'notification_enabled' not in item
    assert 'account_type' not in item


def test_user_detail_is_public_profile_without_private_fields(
    api_client,
    api_request,
    participant_backend_user,
    python_skill,
):
    UserSkill.objects.create(
        user=participant_backend_user,
        skill=python_skill,
        level='basic',
    )

    response = api_request(
        api_client,
        'get',
        f'/api/v1/users/{participant_backend_user.pk}/',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == participant_backend_user.pk
    assert data['specialization_name'] == 'Backend'
    assert data['skills'][0]['name'] == 'Python'
    assert data['contacts_visible'] is False
    assert 'email' not in data
    assert 'notification_enabled' not in data
    assert 'account_type' not in data


def test_participant_registration_requires_specialization(api_client, api_request):
    response = api_request(
        api_client,
        'post',
        '/api/v1/users/',
        data={
            'username': 'new_participant',
            'email': 'new_participant@example.com',
            'password': 'StrongPass123!',
            'account_type': 'participant',
        },
    )

    assert response.status_code == 400
    assert 'specialization_id' in response.json()


def test_owner_registration_does_not_require_specialization(api_client, api_request):
    response = api_request(
        api_client,
        'post',
        '/api/v1/users/',
        data={
            'username': 'new_owner',
            'email': 'new_owner@example.com',
            'password': 'StrongPass123!',
            'account_type': 'owner',
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data['username'] == 'new_owner'
    assert data['email'] == 'new_owner@example.com'
    assert data['account_type'] == 'owner'


def test_registration_validates_password_strength(
    api_client,
    api_request,
    backend_specialization,
):
    response = api_request(
        api_client,
        'post',
        '/api/v1/users/',
        data={
            'username': 'weak_user',
            'email': 'weak_user@example.com',
            'password': 'password',
            'account_type': 'participant',
            'specialization_id': backend_specialization.pk,
        },
    )

    assert response.status_code == 400
    assert 'password' in response.json()


def test_users_me_requires_auth(api_client, api_request):
    response = api_request(api_client, 'get', '/api/v1/users/me/')

    assert response.status_code == 401


def test_current_user_owner_profile_contains_private_fields(
    owner_client,
    api_request,
    owner,
    project,
):
    response = api_request(owner_client, 'get', '/api/v1/users/me/')

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == owner.pk
    assert data['account_type'] == 'owner'
    assert data['notification_enabled'] is True
    assert project.pk in data['owned_project_ids']
    assert 'contacts_visible' not in data


def test_current_user_participant_profile_contains_specialization_and_skills(
    backend_client,
    api_request,
    participant_backend_user,
    django_skill,
):
    UserSkill.objects.create(
        user=participant_backend_user,
        skill=django_skill,
        level='middle',
    )

    response = api_request(backend_client, 'get', '/api/v1/users/me/')

    assert response.status_code == 200
    data = response.json()
    assert data['account_type'] == 'participant'
    assert data['specialization_id'] == participant_backend_user.specialization_id
    assert data['skills'][0]['name'] == 'Django'


def test_user_can_patch_current_profile(
    backend_client,
    api_request,
    participant_backend_user,
    python_skill,
):
    response = api_request(
        backend_client,
        'patch',
        '/api/v1/users/me/',
        data={
            'bio': 'Updated bio',
            'city': 'Moscow',
            'skills': [{'skill_id': python_skill.pk, 'level': 'basic'}],
        },
    )

    assert response.status_code == 200
    participant_backend_user.refresh_from_db()
    assert participant_backend_user.bio == 'Updated bio'
    assert participant_backend_user.city == 'Moscow'
    assert participant_backend_user.skills.get().skill_id == python_skill.pk


def test_participant_cannot_remove_specialization(backend_client, api_request):
    response = api_request(
        backend_client,
        'patch',
        '/api/v1/users/me/',
        data={'specialization_id': None},
    )

    assert response.status_code == 400
    assert 'specialization_id' in response.json()


def test_active_membership_blocks_specialization_change(
    member_client,
    api_request,
    backend_specialization,
    active_membership,
):
    response = api_request(
        member_client,
        'patch',
        '/api/v1/users/me/',
        data={'specialization_id': backend_specialization.pk},
    )

    assert response.status_code == 400


def test_pending_application_blocks_specialization_change(
    backend_client,
    api_request,
    designer_specialization,
    pending_application,
):
    response = api_request(
        backend_client,
        'patch',
        '/api/v1/users/me/',
        data={'specialization_id': designer_specialization.pk},
    )

    assert response.status_code == 400


def test_pending_invitation_blocks_specialization_change(
    designer_client,
    api_request,
    backend_specialization,
    pending_invitation,
):
    response = api_request(
        designer_client,
        'patch',
        '/api/v1/users/me/',
        data={'specialization_id': backend_specialization.pk},
    )

    assert response.status_code == 400


@pytest.mark.parametrize('membership_status', ['left', 'removed'])
def test_historical_membership_does_not_block_specialization_change(
    member_client,
    api_request,
    backend_specialization,
    active_membership,
    participant_member_user,
    membership_status,
):
    active_membership.status = membership_status
    active_membership.save(update_fields=('status',))

    response = api_request(
        member_client,
        'patch',
        '/api/v1/users/me/',
        data={'specialization_id': backend_specialization.pk},
    )

    assert response.status_code == 200
    participant_member_user.refresh_from_db()
    assert participant_member_user.specialization_id == backend_specialization.pk


@pytest.mark.parametrize('interest_status', ['accepted', 'rejected'])
def test_historical_interest_does_not_block_specialization_change(
    backend_client,
    api_request,
    participant_backend_user,
    backend_project_role,
    designer_specialization,
    interest_status,
):
    RoleInterest.objects.create(
        user=participant_backend_user,
        project_role=backend_project_role,
        source=RoleInterest.Source.APPLICATION,
        status=interest_status,
    )

    response = api_request(
        backend_client,
        'patch',
        '/api/v1/users/me/',
        data={'specialization_id': designer_specialization.pk},
    )

    assert response.status_code == 200
    participant_backend_user.refresh_from_db()
    assert participant_backend_user.specialization_id == designer_specialization.pk


def test_owner_can_stay_without_specialization(owner_client, api_request):
    response = api_request(
        owner_client,
        'patch',
        '/api/v1/users/me/',
        data={'specialization_id': None},
    )

    assert response.status_code == 200
    assert response.json()['specialization_id'] is None


def test_my_projects_returns_active_memberships_and_pending_invitations(
    member_client,
    api_request,
    active_membership,
    pending_invitation,
    participant_member_user,
):
    pending_invitation.user = participant_member_user
    pending_invitation.save(update_fields=('user',))

    response = api_request(member_client, 'get', '/api/v1/users/me/projects/')

    assert response.status_code == 200
    data = response.json()
    assert any(item['id'] == active_membership.pk for item in data['memberships'])
    assert any(item['id'] == pending_invitation.pk for item in data['invitations'])


def test_my_projects_excludes_historical_memberships(
    member_client,
    api_request,
    active_membership,
):
    active_membership.status = ProjectMembership.Status.LEFT
    active_membership.save(update_fields=('status',))

    response = api_request(member_client, 'get', '/api/v1/users/me/projects/')

    assert response.status_code == 200
    assert response.json()['memberships'] == []


def test_my_applications_returns_pending_applications(
    backend_client,
    api_request,
    pending_application,
):
    response = api_request(backend_client, 'get', '/api/v1/users/me/applications/')

    assert response.status_code == 200
    assert any(item['id'] == pending_application.pk for item in response.json())


def test_owner_notifications_return_pending_applications(
    owner_client,
    api_request,
    pending_application,
):
    response = api_request(owner_client, 'get', '/api/v1/users/me/notifications/')

    assert response.status_code == 200
    assert any(item['id'] == pending_application.pk for item in response.json())


def test_participant_notifications_return_pending_invitations(
    designer_client,
    api_request,
    pending_invitation,
):
    response = api_request(designer_client, 'get', '/api/v1/users/me/notifications/')

    assert response.status_code == 200
    assert any(item['id'] == pending_invitation.pk for item in response.json())
