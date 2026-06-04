import pytest

from users.models import PortfolioWork


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ('method', 'path'),
    [
        ('get', '/api/v1/users/me/portfolio-works/'),
        ('post', '/api/v1/users/me/portfolio-works/'),
        ('patch', '/api/v1/users/me/portfolio-works/1/'),
        ('delete', '/api/v1/users/me/portfolio-works/1/'),
    ],
)
def test_portfolio_work_endpoints_require_auth(
    api_client,
    api_request,
    method,
    path,
):
    response = api_request(api_client, method, path)

    assert response.status_code == 401


def test_user_sees_only_own_portfolio_works(
    backend_client,
    api_request,
    portfolio_work,
    participant_designer_user,
):
    other_work = PortfolioWork.objects.create(
        user=participant_designer_user,
        title='Other work',
    )

    response = api_request(
        backend_client,
        'get',
        '/api/v1/users/me/portfolio-works/',
    )

    assert response.status_code == 200
    ids = {item['id'] for item in response.json()}
    assert portfolio_work.pk in ids
    assert other_work.pk not in ids


def test_create_portfolio_work_assigns_current_user(
    backend_client,
    api_request,
    participant_backend_user,
):
    response = api_request(
        backend_client,
        'post',
        '/api/v1/users/me/portfolio-works/',
        data={
            'title': 'API project',
            'task': 'Build API',
            'solution': 'Django REST Framework',
            'technologies': ['Python', 'Django'],
            'link': 'https://example.com/api',
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data['id']
    work = PortfolioWork.objects.get(pk=data['id'])
    assert work.user_id == participant_backend_user.pk


def test_portfolio_work_response_contains_contract_fields(
    backend_client,
    api_request,
    portfolio_work,
):
    response = api_request(
        backend_client,
        'get',
        '/api/v1/users/me/portfolio-works/',
    )

    assert response.status_code == 200
    item = next(item for item in response.json() if item['id'] == portfolio_work.pk)
    for field in (
        'id',
        'title',
        'task',
        'solution',
        'image',
        'technologies',
        'link',
        'created_at',
        'updated_at',
    ):
        assert field in item


def test_user_can_update_own_portfolio_work(
    backend_client,
    api_request,
    portfolio_work,
):
    response = api_request(
        backend_client,
        'patch',
        f'/api/v1/users/me/portfolio-works/{portfolio_work.pk}/',
        data={'title': 'Updated portfolio'},
    )

    assert response.status_code == 200
    portfolio_work.refresh_from_db()
    assert portfolio_work.title == 'Updated portfolio'


def test_user_cannot_update_foreign_portfolio_work(
    backend_client,
    api_request,
    participant_designer_user,
):
    foreign_work = PortfolioWork.objects.create(
        user=participant_designer_user,
        title='Foreign work',
    )

    response = api_request(
        backend_client,
        'patch',
        f'/api/v1/users/me/portfolio-works/{foreign_work.pk}/',
        data={'title': 'Illegal update'},
    )

    assert response.status_code == 404


def test_user_can_delete_own_portfolio_work(
    backend_client,
    api_request,
    portfolio_work,
):
    response = api_request(
        backend_client,
        'delete',
        f'/api/v1/users/me/portfolio-works/{portfolio_work.pk}/',
    )

    assert response.status_code == 204
    assert not PortfolioWork.objects.filter(pk=portfolio_work.pk).exists()


def test_user_cannot_delete_foreign_portfolio_work(
    backend_client,
    api_request,
    participant_designer_user,
):
    foreign_work = PortfolioWork.objects.create(
        user=participant_designer_user,
        title='Foreign work',
    )

    response = api_request(
        backend_client,
        'delete',
        f'/api/v1/users/me/portfolio-works/{foreign_work.pk}/',
    )

    assert response.status_code == 404
    assert PortfolioWork.objects.filter(pk=foreign_work.pk).exists()


def test_base64_image_is_accepted_for_portfolio_work(
    backend_client,
    api_request,
    base64_image,
):
    response = api_request(
        backend_client,
        'post',
        '/api/v1/users/me/portfolio-works/',
        data={'title': 'Image work', 'image': base64_image},
    )

    assert response.status_code == 201
    assert response.json()['image']
