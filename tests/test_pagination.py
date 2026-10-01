import pytest

from projects.models import Project, RoleInterest


pytestmark = pytest.mark.django_db


def assert_paginated_response(data):
    assert set(data) == {'count', 'next', 'previous', 'results'}
    assert isinstance(data['results'], list)


def create_projects(owner, field, count, **extra):
    projects = []
    for index in range(count):
        projects.append(
            Project.objects.create(
                owner=owner,
                field=field,
                title=f'Paginated project {index}',
                description='Project description',
                problem='Project problem',
                status=Project.Status.OPEN,
                **extra,
            )
        )
    return projects


def create_applications(create_user, project_role, count):
    applications = []
    for _ in range(count):
        user = create_user(
            account_type='participant',
            specialization=project_role.specialization,
        )
        applications.append(
            RoleInterest.objects.create(
                user=user,
                project_role=project_role,
                source=RoleInterest.Source.APPLICATION,
                status=RoleInterest.Status.PENDING,
            )
        )
    return applications


def test_user_list_uses_global_pagination_defaults_and_page_param(
    api_client,
    api_request,
    create_user,
):
    for _ in range(12):
        create_user(account_type='owner')

    response = api_request(api_client, 'get', '/api/v1/users/')

    assert response.status_code == 200
    data = response.json()
    assert_paginated_response(data)
    assert data['count'] == 12
    assert len(data['results']) == 10
    assert data['next'] is not None
    assert data['previous'] is None

    response = api_request(api_client, 'get', '/api/v1/users/?page=2')

    assert response.status_code == 200
    data = response.json()
    assert_paginated_response(data)
    assert data['count'] == 12
    assert len(data['results']) == 2
    assert data['next'] is None
    assert data['previous'] is not None


def test_user_list_limit_param_changes_page_size(
    api_client,
    api_request,
    create_user,
):
    for _ in range(12):
        create_user(account_type='owner')

    response = api_request(api_client, 'get', '/api/v1/users/?limit=4')

    assert response.status_code == 200
    data = response.json()
    assert_paginated_response(data)
    assert data['count'] == 12
    assert len(data['results']) == 4


def test_featured_projects_action_is_paginated(
    api_client,
    api_request,
    owner,
    field,
):
    create_projects(
        owner,
        field,
        12,
        is_featured=True,
        featured_order=1,
    )

    response = api_request(api_client, 'get', '/api/v1/projects/featured/')

    assert response.status_code == 200
    data = response.json()
    assert_paginated_response(data)
    assert data['count'] == 12
    assert len(data['results']) == 10

    response = api_request(api_client, 'get', '/api/v1/projects/featured/?page=2')

    assert response.status_code == 200
    data = response.json()
    assert_paginated_response(data)
    assert data['count'] == 12
    assert len(data['results']) == 2


def test_project_applications_action_is_paginated_with_limit(
    owner_client,
    api_request,
    project,
    backend_project_role,
    create_user,
):
    create_applications(create_user, backend_project_role, 12)

    response = api_request(
        owner_client,
        'get',
        f'/api/v1/projects/{project.pk}/applications/?limit=5',
    )

    assert response.status_code == 200
    data = response.json()
    assert_paginated_response(data)
    assert data['count'] == 12
    assert len(data['results']) == 5
    assert all(item['source'] == 'application' for item in data['results'])


@pytest.mark.parametrize(
    ('client_fixture', 'path', 'data_fixture'),
    [
        ('api_client', '/api/v1/fields/', 'field'),
        ('api_client', '/api/v1/specializations/', 'backend_specialization'),
        ('api_client', '/api/v1/skills/', 'python_skill'),
        ('backend_client', '/api/v1/users/me/portfolio-works/', 'portfolio_work'),
        ('backend_client', '/api/v1/users/me/favorite-projects/', 'favorite_project'),
        ('api_client', '/api/v1/project-roles/', 'backend_project_role'),
    ],
)
def test_explicitly_unpaginated_endpoints_return_list(
    request,
    api_request,
    client_fixture,
    path,
    data_fixture,
):
    request.getfixturevalue(data_fixture)
    client = request.getfixturevalue(client_fixture)

    response = api_request(client, 'get', path)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
