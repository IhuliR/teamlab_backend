import pytest

from .utils import assert_missing_or_method_not_allowed


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ('method', 'path'),
    [
        ('get', '/api/v1/role-interests/'),
        ('get', '/api/v1/project-memberships/'),
        ('patch', '/api/v1/project-memberships/1/'),
        ('post', '/api/v1/fields/'),
        ('post', '/api/v1/specializations/'),
        ('delete', '/api/v1/users/me/'),
        ('get', '/api/v1/users/me/incoming-interests/'),
        ('get', '/api/v1/users/me/interests/'),
    ],
)
def test_removed_endpoints_do_not_work_as_public_api(
    owner_client,
    api_request,
    method,
    path,
):
    response = api_request(owner_client, method, path)

    assert_missing_or_method_not_allowed(response)
