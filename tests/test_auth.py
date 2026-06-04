import pytest


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


def test_refresh_returns_new_access_token_and_user(
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

    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/refresh/',
        data={'refresh': login_response.json()['refresh']},
    )

    assert response.status_code == 200
    data = response.json()
    assert data['access']
    assert data['user']['id'] == owner.pk
    assert data['user']['username'] == owner.username
    assert data['user']['display_name'] == owner.display_name
    assert data['user']['account_type'] == 'owner'
