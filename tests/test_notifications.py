from django.core import mail
import pytest


pytestmark = pytest.mark.django_db


def test_notifications_are_available_via_api(
    participant_client,
    api_request,
):
    response = api_request(
        participant_client,
        'get',
        '/api/v1/users/me/notifications/',
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_accept_interest_creates_in_app_notification_for_participant(
    owner_client,
    participant_client,
    api_request,
    role_interest,
):
    accept_response = api_request(
        owner_client,
        'post',
        (
            f'/api/v1/project-roles/{role_interest.project_role_id}/'
            f'interests/{role_interest.user_id}/accept/'
        ),
    )
    assert accept_response.status_code == 200

    notifications_response = api_request(
        participant_client,
        'get',
        '/api/v1/users/me/notifications/',
    )

    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    assert any(item.get('type') for item in notifications)
    assert not getattr(mail, 'outbox', [])
