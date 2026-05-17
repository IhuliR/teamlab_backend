import pytest


pytestmark = pytest.mark.django_db


def test_register_user_returns_account_type(api_client, api_request):
    payload = {
        'username': 'new_user',
        'email': 'new_user@example.com',
        'password': 'StrongPass123!',
        'account_type': 'owner',
    }

    response = api_request(api_client, 'post', '/api/v1/users/', data=payload)

    assert response.status_code == 201
    data = response.json()
    assert data['username'] == payload['username']
    assert data['email'] == payload['email']
    assert data['account_type'] == payload['account_type']
    assert 'id' in data


def test_login_returns_jwt_tokens(api_client, api_request, owner, owner_password):
    payload = {
        'email': owner.email,
        'password': owner_password,
    }

    response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert 'access' in data
    assert 'refresh' in data
    assert data['user']['id'] == owner.pk
    assert data['user']['username'] == owner.username
    assert data['user']['account_type'] == owner.account_type


def test_refresh_returns_access_token_and_user(
    api_client,
    api_request,
    owner,
    owner_password,
):
    login_response = api_request(
        api_client,
        'post',
        '/api/v1/auth/token/login/',
        data={
            'email': owner.email,
            'password': owner_password,
        },
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
    assert 'access' in data
    assert data['user']['id'] == owner.pk
    assert data['user']['username'] == owner.username
    assert data['user']['account_type'] == owner.account_type


def test_register_rejects_multiple_account_types_in_one_user(api_client, api_request):
    payload = {
        'username': 'invalid_user',
        'email': 'invalid_user@example.com',
        'password': 'StrongPass123!',
        'account_type': ['owner', 'participant'],
    }

    response = api_request(api_client, 'post', '/api/v1/users/', data=payload)

    assert response.status_code == 400
    data = response.json()
    assert 'account_type' in data
    assert isinstance(data['account_type'], list)


def test_user_list_uses_paginated_response(api_client, api_request, participant):
    response = api_request(api_client, 'get', '/api/v1/users/')

    assert response.status_code == 200
    data = response.json()
    assert set(('count', 'next', 'previous', 'results')).issubset(data)
    assert isinstance(data['count'], int)
    assert isinstance(data['results'], list)
    assert any(item['id'] == participant.pk for item in data['results'])
