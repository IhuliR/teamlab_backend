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
