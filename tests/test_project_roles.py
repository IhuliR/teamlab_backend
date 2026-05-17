import pytest


pytestmark = pytest.mark.django_db


def test_owner_can_create_project_role(
    owner_client,
    api_request,
    project,
    role_payload,
):
    response = api_request(
        owner_client,
        'post',
        '/api/v1/project-roles/',
        data=dict(role_payload, project_id=project.pk),
    )

    assert response.status_code == 201
    data = response.json()
    assert data['project_id'] == project.pk
    assert data['capacity'] == role_payload['capacity']
    assert data['is_open'] is True


@pytest.mark.parametrize('capacity', [0, -1])
def test_project_role_capacity_must_be_positive(
    owner_client,
    api_request,
    project,
    role_payload,
    capacity,
):
    payload = dict(role_payload, capacity=capacity)

    response = api_request(
        owner_client,
        'post',
        '/api/v1/project-roles/',
        data=dict(payload, project_id=project.pk),
    )

    assert response.status_code == 400
    data = response.json()
    assert 'capacity' in data
    assert isinstance(data['capacity'], list)


def test_closed_role_rejects_new_interest(
    participant_client,
    api_request,
    closed_project_role,
):
    response = api_request(
        participant_client,
        'post',
        f'/api/v1/project-roles/{closed_project_role.pk}/interests/',
    )

    assert response.status_code == 400
