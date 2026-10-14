from datetime import timedelta

import pytest
from rest_framework_simplejwt.tokens import RefreshToken


pytestmark = pytest.mark.django_db


def test_login_with_username_returns_tokens_and_user(
    api_client,
    api_request,
    owner,
    password,
):
    owner.display_name = 'Owner Display Name'
    owner.save(update_fields=('display_name',))

    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.username, 'password': password},
    )

    assert response.status_code == 200
    data = response.json()
    assert data['access']
    assert data['refresh']
    assert data['user']['id'] == owner.pk
    assert data['user']['username'] == owner.username
    assert data['user']['display_name'] == owner.display_name
    assert data['user']['account_type'] == 'owner'


def test_display_name_is_not_login_identifier(
    api_client,
    api_request,
    owner,
    password,
):
    owner.display_name = 'Owner Display Name'
    owner.save(update_fields=('display_name',))

    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.display_name, 'password': password},
    )

    assert response.status_code in (400, 401)


def test_login_with_email_is_not_primary_happy_path(
    api_client,
    api_request,
    owner,
    password,
):
    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'email': owner.email, 'password': password},
    )

    assert response.status_code in (400, 401)


def test_login_with_wrong_password_returns_auth_error(
    api_client,
    api_request,
    owner,
):
    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.username, 'password': 'WrongPass123!'},
    )

    assert response.status_code in (400, 401)


def test_refresh_rotates_token_pair_and_blacklists_previous_refresh(
    api_client,
    api_request,
    owner,
    password,
):
    login_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.username, 'password': password},
    )
    assert login_response.status_code == 200
    first_refresh = login_response.json()['refresh']

    first_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/refresh/',
        data={'refresh': first_refresh},
    )

    assert first_response.status_code == 200
    data = first_response.json()
    assert data['access']
    assert data['refresh']
    assert data['refresh'] != first_refresh
    assert data['user']['id'] == owner.pk
    assert data['user']['username'] == owner.username
    assert data['user']['display_name'] == owner.display_name
    assert data['user']['account_type'] == 'owner'

    reused_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/refresh/',
        data={'refresh': first_refresh},
    )

    assert reused_response.status_code == 401

    second_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/refresh/',
        data={'refresh': data['refresh']},
    )

    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data['access']
    assert second_data['refresh']
    assert second_data['user']['id'] == owner.pk


def test_refresh_for_deleted_user_returns_auth_error(
    api_client,
    api_request,
    owner,
    password,
):
    login_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.username, 'password': password},
    )
    assert login_response.status_code == 200
    refresh = login_response.json()['refresh']
    owner.delete()

    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/refresh/',
        data={'refresh': refresh},
    )

    assert response.status_code == 401


def test_logout_blacklists_refresh_but_access_remains_valid(
    api_client,
    api_request,
    owner,
    password,
):
    login_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.username, 'password': password},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    logout_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/blacklist/',
        data={'refresh': tokens['refresh']},
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {}

    refresh_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/refresh/',
        data={'refresh': tokens['refresh']},
    )
    assert refresh_response.status_code == 401

    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
    )
    current_user_response = api_request(
        api_client,
        'get',
        '/api/v1/users/me/',
    )
    assert current_user_response.status_code == 200
    assert current_user_response.json()['id'] == owner.pk


@pytest.mark.parametrize(
    ('refresh', 'expected_status'),
    (
        ('not-a-jwt', 401),
        ('', 400),
    ),
)
def test_logout_rejects_invalid_refresh(
    api_client,
    api_request,
    refresh,
    expected_status,
):
    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/blacklist/',
        data={'refresh': refresh},
    )

    assert response.status_code == expected_status
    if expected_status == 401:
        assert response.json()['code'] == 'token_not_valid'
    else:
        assert 'refresh' in response.json()


def test_logout_rejects_expired_refresh(
    api_client,
    api_request,
    owner,
):
    refresh = RefreshToken.for_user(owner)
    refresh.set_exp(lifetime=timedelta(seconds=-1))

    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/blacklist/',
        data={'refresh': str(refresh)},
    )

    assert response.status_code == 401
    assert response.json()['code'] == 'token_not_valid'


def test_repeated_logout_returns_auth_error(
    api_client,
    api_request,
    owner,
    password,
):
    login_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.username, 'password': password},
    )
    refresh = login_response.json()['refresh']

    first_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/blacklist/',
        data={'refresh': refresh},
    )
    repeated_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/blacklist/',
        data={'refresh': refresh},
    )

    assert first_response.status_code == 200
    assert repeated_response.status_code == 401
    assert repeated_response.json()['code'] == 'token_not_valid'


def test_logout_does_not_revoke_another_session(
    api_client,
    api_request,
    owner,
    password,
):
    first_login = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.username, 'password': password},
    )
    second_login = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={'username': owner.username, 'password': password},
    )
    first_refresh = first_login.json()['refresh']
    second_refresh = second_login.json()['refresh']

    logout_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/blacklist/',
        data={'refresh': first_refresh},
    )
    revoked_session_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/refresh/',
        data={'refresh': first_refresh},
    )
    active_session_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/refresh/',
        data={'refresh': second_refresh},
    )

    assert logout_response.status_code == 200
    assert revoked_session_response.status_code == 401
    assert active_session_response.status_code == 200
