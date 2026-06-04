import pytest

from projects.models import ProjectMembership, ProjectRole, RoleInterest


pytestmark = pytest.mark.django_db


def test_owner_can_create_role_in_own_project(
    owner_client,
    api_request,
    project,
    role_payload,
):
    response = api_request(
        owner_client,
        'post',
        '/api/v1/project-roles/',
        data=role_payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data['project_id'] == project.pk
    assert data['specialization_id'] == role_payload['specialization_id']
    assert data['tasks'] == role_payload['tasks']
    assert data['benefits'] == role_payload['benefits']
    assert len(data['skills']) == 1


def test_non_owner_cannot_create_role_in_foreign_project(
    backend_client,
    api_request,
    role_payload,
):
    response = api_request(
        backend_client,
        'post',
        '/api/v1/project-roles/',
        data=role_payload,
    )

    assert response.status_code == 403


def test_cannot_create_duplicate_role_specialization(
    owner_client,
    api_request,
    project,
    backend_project_role,
    role_payload,
):
    payload = dict(
        role_payload,
        specialization_id=backend_project_role.specialization_id,
    )

    response = api_request(
        owner_client,
        'post',
        '/api/v1/project-roles/',
        data=payload,
    )

    assert response.status_code == 400
    assert ProjectRole.objects.filter(
        project=project,
        specialization=backend_project_role.specialization,
    ).count() == 1


def test_owner_can_patch_role_in_own_project(
    owner_client,
    api_request,
    backend_project_role,
):
    response = api_request(
        owner_client,
        'patch',
        f'/api/v1/project-roles/{backend_project_role.pk}/',
        data={'tasks': ['Updated task']},
    )

    assert response.status_code == 200
    backend_project_role.refresh_from_db()
    assert backend_project_role.tasks == ['Updated task']


def test_non_owner_cannot_patch_foreign_project_role(
    backend_client,
    api_request,
    backend_project_role,
):
    response = api_request(
        backend_client,
        'patch',
        f'/api/v1/project-roles/{backend_project_role.pk}/',
        data={'tasks': ['Illegal update']},
    )

    assert response.status_code == 403


def test_owner_can_delete_role_without_blocking_records(
    owner_client,
    api_request,
    designer_project_role,
):
    response = api_request(
        owner_client,
        'delete',
        f'/api/v1/project-roles/{designer_project_role.pk}/',
    )

    assert response.status_code == 204
    assert not ProjectRole.objects.filter(pk=designer_project_role.pk).exists()


def test_role_delete_blocked_by_active_membership(
    owner_client,
    api_request,
    active_membership,
):
    response = api_request(
        owner_client,
        'delete',
        f'/api/v1/project-roles/{active_membership.project_role_id}/',
    )

    assert response.status_code == 400


def test_role_delete_blocked_by_pending_application(
    owner_client,
    api_request,
    pending_application,
):
    response = api_request(
        owner_client,
        'delete',
        f'/api/v1/project-roles/{pending_application.project_role_id}/',
    )

    assert response.status_code == 400


def test_role_delete_blocked_by_pending_invitation(
    owner_client,
    api_request,
    pending_invitation,
):
    response = api_request(
        owner_client,
        'delete',
        f'/api/v1/project-roles/{pending_invitation.project_role_id}/',
    )

    assert response.status_code == 400


def test_historical_records_do_not_block_role_delete(
    owner_client,
    api_request,
    participant_designer_user,
    designer_project_role,
):
    rejected = RoleInterest.objects.create(
        user=participant_designer_user,
        project_role=designer_project_role,
        source=RoleInterest.Source.INVITATION,
        status=RoleInterest.Status.REJECTED,
    )

    response = api_request(
        owner_client,
        'delete',
        f'/api/v1/project-roles/{designer_project_role.pk}/',
    )

    assert response.status_code == 204
    assert not RoleInterest.objects.filter(pk=rejected.pk).exists()


def test_historical_membership_does_not_block_role_delete(
    owner_client,
    api_request,
    active_membership,
):
    role_id = active_membership.project_role_id
    interest_id = active_membership.role_interest_id
    active_membership.status = ProjectMembership.Status.LEFT
    active_membership.save(update_fields=('status',))

    response = api_request(
        owner_client,
        'delete',
        f'/api/v1/project-roles/{role_id}/',
    )

    assert response.status_code == 204
    assert not ProjectRole.objects.filter(pk=role_id).exists()
    assert not RoleInterest.objects.filter(pk=interest_id).exists()
