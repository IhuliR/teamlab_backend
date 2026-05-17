import pytest


pytestmark = pytest.mark.django_db


def assert_paginated_response(data):
    assert set(('count', 'next', 'previous', 'results')).issubset(data)
    assert isinstance(data['count'], int)
    assert isinstance(data['results'], list)


def test_my_projects_requires_authentication(api_client, api_request):
    response = api_request(api_client, 'get', '/api/v1/users/me/projects/')

    assert response.status_code == 401
    data = response.json()
    assert 'detail' in data
    assert isinstance(data['detail'], str)


def test_my_projects_uses_paginated_response_for_owner(
    owner_client,
    api_request,
    project,
):
    response = api_request(owner_client, 'get', '/api/v1/users/me/projects/')

    assert response.status_code == 200
    data = response.json()
    assert_paginated_response(data)
    assert any(
        item['id'] == project.pk
        and item['relation'] == 'owner'
        for item in data['results']
    )
