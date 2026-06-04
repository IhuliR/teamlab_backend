import pytest

from projects.models import ProjectMembership, RoleInterest

from .utils import assert_missing_or_method_not_allowed


pytestmark = pytest.mark.django_db


def test_owner_can_list_project_applications(
    owner_client,
    api_request,
    project,
    pending_application,
):
    response = api_request(
        owner_client,
        'get',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code == 200
    assert any(item['id'] == pending_application.pk for item in response.json())


def test_non_owner_cannot_list_project_applications(
    backend_client,
    api_request,
    project,
):
    response = api_request(
        backend_client,
        'get',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code == 403


def test_anonymous_cannot_list_project_applications(api_client, api_request, project):
    response = api_request(
        api_client,
        'get',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code == 401


def test_participant_can_create_application_without_body(
    backend_client,
    api_request,
    participant_backend_user,
    project,
    backend_project_role,
):
    response = api_request(
        backend_client,
        'post',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code == 201
    data = response.json()
    assert data['user_id'] == participant_backend_user.pk
    assert data['project_role_id'] == backend_project_role.pk
    assert data['source'] == 'application'
    assert data['status'] == 'pending'


def test_anonymous_cannot_create_application(api_client, api_request, project):
    response = api_request(
        api_client,
        'post',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code == 401


def test_owner_cannot_apply_to_own_project(owner_client, api_request, project):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code in (400, 403)


def test_participant_without_matching_role_cannot_apply(
    designer_client,
    api_request,
    project,
    backend_project_role,
):
    response = api_request(
        designer_client,
        'post',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code == 400


def test_duplicate_application_is_not_created(
    backend_client,
    api_request,
    project,
    pending_application,
):
    before_count = RoleInterest.objects.count()

    response = api_request(
        backend_client,
        'post',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code in (400, 409)
    assert RoleInterest.objects.count() == before_count


@pytest.mark.parametrize('historical_status', ['accepted', 'rejected'])
def test_historical_application_blocks_repeated_application(
    backend_client,
    api_request,
    participant_backend_user,
    project,
    backend_project_role,
    historical_status,
):
    RoleInterest.objects.create(
        user=participant_backend_user,
        project_role=backend_project_role,
        source=RoleInterest.Source.APPLICATION,
        status=historical_status,
    )

    response = api_request(
        backend_client,
        'post',
        f'/api/v1/projects/{project.pk}/applications/',
    )

    assert response.status_code in (400, 409)
    assert RoleInterest.objects.filter(
        user=participant_backend_user,
        project_role=backend_project_role,
    ).count() == 1


def test_owner_can_list_project_invitations(
    owner_client,
    api_request,
    project,
    pending_invitation,
):
    response = api_request(
        owner_client,
        'get',
        f'/api/v1/projects/{project.pk}/invitations/',
    )

    assert response.status_code == 200
    assert any(item['id'] == pending_invitation.pk for item in response.json())


def test_non_owner_cannot_list_project_invitations(
    backend_client,
    api_request,
    project,
):
    response = api_request(
        backend_client,
        'get',
        f'/api/v1/projects/{project.pk}/invitations/',
    )

    assert response.status_code == 403


def test_owner_can_create_invitation_by_user_id(
    owner_client,
    api_request,
    participant_designer_user,
    project,
    designer_project_role,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/projects/{project.pk}/invitations/',
        data={'user_id': participant_designer_user.pk},
    )

    assert response.status_code == 201
    data = response.json()
    assert data['user_id'] == participant_designer_user.pk
    assert data['project_role_id'] == designer_project_role.pk
    assert data['source'] == 'invitation'
    assert data['status'] == 'pending'


def test_non_owner_cannot_create_invitation(
    backend_client,
    api_request,
    participant_designer_user,
    project,
):
    response = api_request(
        backend_client,
        'post',
        f'/api/v1/projects/{project.pk}/invitations/',
        data={'user_id': participant_designer_user.pk},
    )

    assert response.status_code == 403


def test_user_without_matching_role_cannot_be_invited(
    owner_client,
    api_request,
    participant_designer_user,
    project,
    backend_project_role,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/projects/{project.pk}/invitations/',
        data={'user_id': participant_designer_user.pk},
    )

    assert response.status_code == 400


def test_duplicate_invitation_is_not_created(
    owner_client,
    api_request,
    participant_designer_user,
    project,
    pending_invitation,
):
    before_count = RoleInterest.objects.count()

    response = api_request(
        owner_client,
        'post',
        f'/api/v1/projects/{project.pk}/invitations/',
        data={'user_id': participant_designer_user.pk},
    )

    assert response.status_code in (400, 409)
    assert RoleInterest.objects.count() == before_count


@pytest.mark.parametrize('historical_status', ['accepted', 'rejected'])
def test_historical_invitation_blocks_repeated_invitation(
    owner_client,
    api_request,
    participant_designer_user,
    project,
    designer_project_role,
    historical_status,
):
    RoleInterest.objects.create(
        user=participant_designer_user,
        project_role=designer_project_role,
        source=RoleInterest.Source.INVITATION,
        status=historical_status,
    )

    response = api_request(
        owner_client,
        'post',
        f'/api/v1/projects/{project.pk}/invitations/',
        data={'user_id': participant_designer_user.pk},
    )

    assert response.status_code in (400, 409)
    assert RoleInterest.objects.filter(
        user=participant_designer_user,
        project_role=designer_project_role,
    ).count() == 1


def test_owner_accepts_application_and_membership_is_created(
    owner_client,
    api_request,
    pending_application,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{pending_application.pk}/accept/',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'accepted'
    assert data['membership_id']
    assert data['membership_status'] == 'active'
    pending_application.refresh_from_db()
    assert pending_application.status == RoleInterest.Status.ACCEPTED
    assert ProjectMembership.objects.filter(
        role_interest=pending_application,
        status=ProjectMembership.Status.ACTIVE,
    ).exists()


def test_applicant_cannot_accept_own_application(
    backend_client,
    api_request,
    pending_application,
):
    response = api_request(
        backend_client,
        'post',
        f'/api/v1/role-interests/{pending_application.pk}/accept/',
    )

    assert response.status_code == 403


def test_owner_rejects_application_without_membership(
    owner_client,
    api_request,
    pending_application,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{pending_application.pk}/reject/',
    )

    assert response.status_code == 200
    assert response.json()['status'] == 'rejected'
    pending_application.refresh_from_db()
    assert pending_application.status == RoleInterest.Status.REJECTED
    assert not ProjectMembership.objects.filter(
        role_interest=pending_application,
    ).exists()


def test_invited_user_accepts_invitation_and_membership_is_created(
    designer_client,
    api_request,
    pending_invitation,
):
    response = api_request(
        designer_client,
        'post',
        f'/api/v1/role-interests/{pending_invitation.pk}/accept/',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'accepted'
    assert data['membership_id']
    assert data['membership_status'] == 'active'


def test_owner_cannot_accept_invitation_for_user(
    owner_client,
    api_request,
    pending_invitation,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{pending_invitation.pk}/accept/',
    )

    assert response.status_code == 403


def test_invited_user_rejects_invitation_without_membership(
    designer_client,
    api_request,
    pending_invitation,
):
    response = api_request(
        designer_client,
        'post',
        f'/api/v1/role-interests/{pending_invitation.pk}/reject/',
    )

    assert response.status_code == 200
    assert response.json()['status'] == 'rejected'
    assert not ProjectMembership.objects.filter(
        role_interest=pending_invitation,
    ).exists()


@pytest.mark.parametrize('action', ['accept', 'reject'])
def test_cannot_process_non_pending_role_interest(
    owner_client,
    api_request,
    accepted_role_interest,
    action,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/role-interests/{accepted_role_interest.pk}/{action}/',
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    ('method', 'path'),
    [
        ('get', '/api/v1/role-interests/'),
        ('post', '/api/v1/role-interests/1/cancel/'),
        ('post', '/api/v1/role-interests/1/cancelled/'),
    ],
)
def test_removed_role_interest_endpoints_are_not_available(
    api_client,
    api_request,
    method,
    path,
):
    response = api_request(api_client, method, path)

    assert_missing_or_method_not_allowed(response)
