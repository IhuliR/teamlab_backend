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


def test_role_create_rejects_duplicate_skill_id(
    owner_client,
    api_request,
    role_payload,
):
    skill = role_payload['skills'][0]
    payload = dict(
        role_payload,
        skills=[
            skill,
            dict(skill, order=2),
        ],
    )

    response = api_request(
        owner_client,
        'post',
        '/api/v1/project-roles/',
        data=payload,
    )

    assert response.status_code == 400
    assert ProjectRole.objects.filter(
        project_id=role_payload['project_id'],
        specialization_id=role_payload['specialization_id'],
    ).count() == 0


def test_role_create_rejects_duplicate_skill_order(
    owner_client,
    api_request,
    role_payload,
    python_skill,
):
    skill = role_payload['skills'][0]
    payload = dict(
        role_payload,
        skills=[
            skill,
            {
                'skill_id': python_skill.pk,
                'description': 'Python support',
                'order': skill['order'],
            },
        ],
    )

    response = api_request(
        owner_client,
        'post',
        '/api/v1/project-roles/',
        data=payload,
    )

    assert response.status_code == 400
    assert ProjectRole.objects.filter(
        project_id=role_payload['project_id'],
        specialization_id=role_payload['specialization_id'],
    ).count() == 0


def test_role_create_rejects_non_positive_skill_order(
    owner_client,
    api_request,
    role_payload,
):
    skill = role_payload['skills'][0]
    payload = dict(
        role_payload,
        skills=[dict(skill, order=0)],
    )

    response = api_request(
        owner_client,
        'post',
        '/api/v1/project-roles/',
        data=payload,
    )

    assert response.status_code == 400


def test_role_update_rejects_duplicate_skill_order(
    owner_client,
    api_request,
    backend_project_role,
    python_skill,
    django_skill,
):
    response = api_request(
        owner_client,
        'patch',
        f'/api/v1/project-roles/{backend_project_role.pk}/',
        data={
            'skills': [
                {
                    'skill_id': python_skill.pk,
                    'description': 'Python backend',
                    'order': 1,
                },
                {
                    'skill_id': django_skill.pk,
                    'description': 'Django backend',
                    'order': 1,
                },
            ],
        },
    )

    assert response.status_code == 400


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


def test_project_roles_can_be_filtered_by_project_id(
    api_client,
    api_request,
    project,
    another_project,
    backend_project_role,
    designer_project_role,
):
    response = api_request(
        api_client,
        'get',
        f'/api/v1/project-roles/?project_id={project.pk}',
    )

    assert response.status_code == 200
    ids = {item['id'] for item in response.json()}
    assert backend_project_role.pk in ids
    assert designer_project_role.pk in ids

    response = api_request(
        api_client,
        'get',
        f'/api/v1/project-roles/?project_id={another_project.pk}',
    )

    assert response.status_code == 200
    assert response.json() == []


def test_project_roles_can_be_filtered_by_specialization_id(
    api_client,
    api_request,
    backend_project_role,
    designer_project_role,
):
    response = api_request(
        api_client,
        'get',
        (
            '/api/v1/project-roles/?specialization_id='
            f'{backend_project_role.specialization_id}'
        ),
    )

    assert response.status_code == 200
    ids = {item['id'] for item in response.json()}
    assert backend_project_role.pk in ids
    assert designer_project_role.pk not in ids


def test_project_roles_can_be_filtered_by_project_and_specialization(
    api_client,
    api_request,
    project,
    backend_project_role,
    designer_project_role,
):
    response = api_request(
        api_client,
        'get',
        (
            f'/api/v1/project-roles/?project_id={project.pk}'
            f'&specialization_id={backend_project_role.specialization_id}'
        ),
    )

    assert response.status_code == 200
    ids = [item['id'] for item in response.json()]
    assert ids == [backend_project_role.pk]

    response = api_request(
        api_client,
        'get',
        (
            f'/api/v1/project-roles/?project_id={project.pk}'
            '&specialization_id=999999'
        ),
    )

    assert response.status_code == 200
    assert response.json() == []
