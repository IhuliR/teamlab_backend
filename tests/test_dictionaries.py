import pytest

from projects.models import Field, Specialization
from users.models import Skill

from .utils import assert_missing_or_method_not_allowed, results


pytestmark = pytest.mark.django_db


def test_fields_list_is_public(api_client, api_request, field):
    response = api_request(api_client, 'get', '/api/v1/fields/')

    assert response.status_code == 200
    items = results(response.json())
    assert any(item['id'] == field.pk for item in items)


def test_featured_fields_are_public_filtered_and_ordered(
    api_client,
    api_request,
    field,
    featured_field,
    first_featured_field,
):
    response = api_request(api_client, 'get', '/api/v1/fields/featured/')

    assert response.status_code == 200
    ids = [item['id'] for item in response.json()]
    assert first_featured_field.pk in ids
    assert featured_field.pk in ids
    assert field.pk not in ids
    assert ids.index(first_featured_field.pk) < ids.index(featured_field.pk)


def test_specializations_list_is_public(
    api_client,
    api_request,
    backend_specialization,
):
    response = api_request(api_client, 'get', '/api/v1/specializations/')

    assert response.status_code == 200
    items = results(response.json())
    assert any(item['id'] == backend_specialization.pk for item in items)


def test_skills_list_is_public(api_client, api_request, python_skill):
    response = api_request(api_client, 'get', '/api/v1/skills/')

    assert response.status_code == 200
    items = results(response.json())
    assert any(item['id'] == python_skill.pk for item in items)


def test_authenticated_user_can_create_skill(owner_client, api_request):
    response = api_request(
        owner_client,
        'post',
        '/api/v1/skills/',
        data={'name': 'FastAPI'},
    )

    assert response.status_code == 201
    assert response.json()['name'] == 'FastAPI'
    assert Skill.objects.filter(name='FastAPI').exists()


def test_anonymous_user_cannot_create_skill(api_client, api_request):
    response = api_request(
        api_client,
        'post',
        '/api/v1/skills/',
        data={'name': 'Go'},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    ('path', 'model', 'payload'),
    [
        ('/api/v1/fields/', Field, {'name': 'Public field'}),
        (
            '/api/v1/specializations/',
            Specialization,
            {'name': 'Public specialization', 'field_id': 1},
        ),
    ],
)
def test_system_dictionaries_are_not_publicly_created(
    owner_client,
    api_request,
    path,
    model,
    payload,
):
    before_count = model.objects.count()

    response = api_request(owner_client, 'post', path, data=payload)

    assert_missing_or_method_not_allowed(response)
    assert model.objects.count() == before_count
