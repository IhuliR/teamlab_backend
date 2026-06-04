import pytest

from projects.models import ProjectMembership

from .utils import assert_missing_or_method_not_allowed


pytestmark = pytest.mark.django_db


def test_active_member_can_leave_project(
    member_client,
    api_request,
    active_membership,
):
    response = api_request(
        member_client,
        'post',
        f'/api/v1/project-memberships/{active_membership.pk}/leave/',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'left'
    assert data['ended_at'] is not None
    active_membership.refresh_from_db()
    assert active_membership.status == ProjectMembership.Status.LEFT
    assert active_membership.ended_at is not None


def test_user_cannot_leave_another_membership(
    backend_client,
    api_request,
    active_membership,
):
    response = api_request(
        backend_client,
        'post',
        f'/api/v1/project-memberships/{active_membership.pk}/leave/',
    )

    assert response.status_code == 403


def test_owner_cannot_leave_for_participant(
    owner_client,
    api_request,
    active_membership,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/project-memberships/{active_membership.pk}/leave/',
    )

    assert response.status_code == 403


def test_cannot_leave_non_active_membership(
    member_client,
    api_request,
    active_membership,
):
    active_membership.status = ProjectMembership.Status.LEFT
    active_membership.save(update_fields=('status',))

    response = api_request(
        member_client,
        'post',
        f'/api/v1/project-memberships/{active_membership.pk}/leave/',
    )

    assert response.status_code == 400


def test_project_owner_can_remove_active_participant(
    owner_client,
    api_request,
    active_membership,
):
    response = api_request(
        owner_client,
        'post',
        f'/api/v1/project-memberships/{active_membership.pk}/remove/',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'removed'
    assert data['ended_at'] is not None
    active_membership.refresh_from_db()
    assert active_membership.status == ProjectMembership.Status.REMOVED
    assert active_membership.ended_at is not None


def test_non_owner_cannot_remove_participant(
    backend_client,
    api_request,
    active_membership,
):
    response = api_request(
        backend_client,
        'post',
        f'/api/v1/project-memberships/{active_membership.pk}/remove/',
    )

    assert response.status_code == 403


def test_member_cannot_remove_self(
    member_client,
    api_request,
    active_membership,
):
    response = api_request(
        member_client,
        'post',
        f'/api/v1/project-memberships/{active_membership.pk}/remove/',
    )

    assert response.status_code == 403


def test_cannot_remove_non_active_membership(
    owner_client,
    api_request,
    active_membership,
):
    active_membership.status = ProjectMembership.Status.REMOVED
    active_membership.save(update_fields=('status',))

    response = api_request(
        owner_client,
        'post',
        f'/api/v1/project-memberships/{active_membership.pk}/remove/',
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    ('method', 'path'),
    [
        ('get', '/api/v1/project-memberships/'),
        ('post', '/api/v1/project-memberships/'),
        ('patch', '/api/v1/project-memberships/1/'),
    ],
)
def test_removed_membership_generic_api_is_not_available(
    owner_client,
    api_request,
    method,
    path,
):
    response = api_request(owner_client, method, path)

    assert_missing_or_method_not_allowed(response)
