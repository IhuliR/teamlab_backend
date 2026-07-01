import pytest

from projects.models import Project, ProjectRole, ProjectRoleSkill

from .utils import results


pytestmark = pytest.mark.django_db


def test_project_list_is_public_and_contains_roles_preview(
    api_client,
    api_request,
    project,
    backend_project_role,
):
    response = api_request(api_client, 'get', '/api/v1/projects/')

    assert response.status_code == 200
    items = results(response.json())
    item = next(item for item in items if item['id'] == project.pk)
    assert 'roles_preview' in item
    assert item['roles_preview'][0]['id'] == backend_project_role.pk


def test_project_detail_is_public_and_contains_roles(
    api_client,
    api_request,
    project,
    backend_project_role,
):
    response = api_request(api_client, 'get', f'/api/v1/projects/{project.pk}/')

    assert response.status_code == 200
    data = response.json()
    assert data['id'] == project.pk
    assert 'roles' in data
    assert data['roles'][0]['id'] == backend_project_role.pk
    for field in (
        'matching_role_id',
        'matching_role_name',
        'my_interest_id',
        'my_interest_status',
        'my_interest_source',
        'my_membership_id',
        'my_membership_status',
    ):
        assert data[field] is None


def test_project_detail_for_participant_returns_matching_role_context(
    backend_client,
    api_request,
    project,
    backend_project_role,
):
    response = api_request(backend_client, 'get', f'/api/v1/projects/{project.pk}/')

    assert response.status_code == 200
    data = response.json()
    assert data['matching_role_id'] == backend_project_role.pk
    assert data['matching_role_name'] == backend_project_role.specialization.name
    assert data['my_interest_id'] is None
    assert data['my_membership_id'] is None


def test_project_detail_for_participant_returns_pending_interest_context(
    backend_client,
    api_request,
    project,
    pending_application,
):
    response = api_request(backend_client, 'get', f'/api/v1/projects/{project.pk}/')

    assert response.status_code == 200
    data = response.json()
    assert data['matching_role_id'] == pending_application.project_role_id
    assert data['my_interest_id'] == pending_application.pk
    assert data['my_interest_status'] == 'pending'
    assert data['my_interest_source'] == 'application'


def test_project_detail_for_member_returns_membership_context(
    member_client,
    api_request,
    project,
    active_membership,
):
    response = api_request(member_client, 'get', f'/api/v1/projects/{project.pk}/')

    assert response.status_code == 200
    data = response.json()
    assert data['matching_role_id'] == active_membership.project_role_id
    assert data['my_membership_id'] == active_membership.pk
    assert data['my_membership_status'] == 'active'


def test_featured_projects_are_public_open_only(
    api_client,
    api_request,
    featured_project,
    closed_featured_project,
    project,
):
    response = api_request(api_client, 'get', '/api/v1/projects/featured/')

    assert response.status_code == 200
    ids = [item['id'] for item in results(response.json())]
    assert featured_project.pk in ids
    assert closed_featured_project.pk not in ids
    assert project.pk not in ids


@pytest.mark.parametrize(
    ('query', 'expected_fixture', 'excluded_fixture'),
    [
        ('search={title}', 'project', 'another_project'),
        ('field_id={field_id}', 'project', 'another_project'),
        ('status=closed', 'closed_project', 'project'),
        ('specialization_ids={specialization_id}', 'project', 'another_project'),
        ('skill_ids={skill_id}', 'project', 'another_project'),
        ('ordering=title', 'project', 'another_project'),
    ],
)
def test_project_list_filters_include_expected_project(
    request,
    api_client,
    api_request,
    query,
    expected_fixture,
    excluded_fixture,
    project,
    another_project,
    closed_project,
    backend_project_role,
    project_role_skill,
):
    expected = request.getfixturevalue(expected_fixture)
    excluded = request.getfixturevalue(excluded_fixture)
    formatted_query = query.format(
        title=project.title,
        field_id=project.field_id,
        specialization_id=backend_project_role.specialization_id,
        skill_id=project_role_skill.skill_id,
    )

    response = api_request(api_client, 'get', f'/api/v1/projects/?{formatted_query}')

    assert response.status_code == 200
    ids = {item['id'] for item in results(response.json())}
    assert expected.pk in ids
    if 'ordering=' not in query:
        assert excluded.pk not in ids


def test_project_list_can_filter_by_multiple_field_ids(
    api_client,
    api_request,
    field,
    another_field,
    project,
    another_project,
):
    response = api_request(
        api_client,
        'get',
        f'/api/v1/projects/?field_ids={field.pk},{another_field.pk}',
    )

    assert response.status_code == 200
    ids = {item['id'] for item in results(response.json())}
    assert project.pk in ids
    assert another_project.pk in ids


def test_project_list_skill_filter_does_not_duplicate_projects(
    api_client,
    api_request,
    project,
    backend_project_role,
    frontend_project_role,
    python_skill,
    django_skill,
):
    ProjectRoleSkill.objects.create(
        project_role=backend_project_role,
        skill=python_skill,
        description='Python backend',
        order=1,
    )
    ProjectRoleSkill.objects.create(
        project_role=frontend_project_role,
        skill=django_skill,
        description='Django frontend',
        order=1,
    )

    response = api_request(
        api_client,
        'get',
        f'/api/v1/projects/?skill_ids={python_skill.pk},{django_skill.pk}',
    )

    assert response.status_code == 200
    ids = [item['id'] for item in results(response.json())]
    assert ids.count(project.pk) == 1


def test_project_list_specialization_filter_does_not_duplicate_projects(
    api_client,
    api_request,
    project,
    backend_project_role,
    frontend_project_role,
):
    response = api_request(
        api_client,
        'get',
        (
            '/api/v1/projects/?specialization_ids='
            f'{backend_project_role.specialization_id},'
            f'{frontend_project_role.specialization_id}'
        ),
    )

    assert response.status_code == 200
    ids = [item['id'] for item in results(response.json())]
    assert ids.count(project.pk) == 1


def test_owner_can_create_project_with_nested_roles(
    owner_client,
    api_request,
    owner,
    project_payload,
):
    response = api_request(
        owner_client,
        'post',
        '/api/v1/projects/',
        data=project_payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data['id']
    assert data['owner_id'] == owner.pk
    assert data['title'] == project_payload['title']
    assert 'roles' in data
    assert len(data['roles']) == 1
    assert data['roles'][0]['specialization_id'] == (
        project_payload['roles'][0]['specialization_id']
    )


def test_participant_cannot_create_project(
    backend_client,
    api_request,
    project_payload,
):
    response = api_request(
        backend_client,
        'post',
        '/api/v1/projects/',
        data=project_payload,
    )

    assert response.status_code == 403


def test_anonymous_cannot_create_project(api_client, api_request, project_payload):
    response = api_request(
        api_client,
        'post',
        '/api/v1/projects/',
        data=project_payload,
    )

    assert response.status_code == 401


def test_project_owner_is_taken_from_request_user(
    owner_client,
    api_request,
    owner,
    participant_backend_user,
    project_payload,
):
    payload = dict(project_payload, owner_id=participant_backend_user.pk)

    response = api_request(
        owner_client,
        'post',
        '/api/v1/projects/',
        data=payload,
    )

    assert response.status_code == 201
    assert response.json()['owner_id'] == owner.pk


def test_project_create_does_not_allow_public_featured_control(
    owner_client,
    api_request,
    project_payload,
):
    payload = dict(project_payload, is_featured=True, featured_order=1)

    response = api_request(
        owner_client,
        'post',
        '/api/v1/projects/',
        data=payload,
    )

    assert response.status_code == 201
    project = Project.objects.get(pk=response.json()['id'])
    assert project.is_featured is False
    assert project.featured_order == 0
    assert 'featured_order' not in response.json()


def test_owner_can_patch_own_project(owner_client, api_request, project):
    response = api_request(
        owner_client,
        'patch',
        f'/api/v1/projects/{project.pk}/',
        data={'title': 'Updated title'},
    )

    assert response.status_code == 200
    project.refresh_from_db()
    assert project.title == 'Updated title'


def test_non_owner_cannot_patch_project(
    designer_client,
    api_request,
    project,
):
    response = api_request(
        designer_client,
        'patch',
        f'/api/v1/projects/{project.pk}/',
        data={'title': 'Illegal update'},
    )

    assert response.status_code == 403


def test_project_patch_does_not_allow_featured_control(
    owner_client,
    api_request,
    project,
):
    response = api_request(
        owner_client,
        'patch',
        f'/api/v1/projects/{project.pk}/',
        data={'is_featured': True, 'featured_order': 1},
    )

    assert response.status_code == 200
    project.refresh_from_db()
    assert project.is_featured is False
    assert project.featured_order == 0


def test_project_create_rejects_duplicate_role_specialization(
    owner_client,
    api_request,
    project_payload,
):
    role = project_payload['roles'][0]
    payload = dict(project_payload, roles=[role, dict(role)])

    response = api_request(
        owner_client,
        'post',
        '/api/v1/projects/',
        data=payload,
    )

    assert response.status_code == 400
    assert ProjectRole.objects.filter(project__title=project_payload['title']).count() == 0
