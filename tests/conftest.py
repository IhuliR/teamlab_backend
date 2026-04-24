import uuid

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.urls import Resolver404, resolve


CRITICAL_MODELS = {
    'Field',
    'Specialization',
    'Skill',
    'Project',
    'ProjectRole',
    'RoleInterest',
}

CRITICAL_RELATIONS = {
    ('Specialization', 'field'): 'Specialization.field is required by DOMAIN_MODEL.md',
    ('Project', 'owner'): 'Project.owner is required by DOMAIN_MODEL.md',
    ('ProjectRole', 'project'): 'ProjectRole.project is part of core flow',
    ('RoleInterest', 'project_role'): 'RoleInterest.project_role is part of core flow',
}


def _model_by_name(model_name):
    for model in apps.get_models():
        if model.__name__ == model_name:
            return model
    if model_name in CRITICAL_MODELS:
        pytest.fail(f'{model_name} model is required by DOMAIN_MODEL.md')
    pytest.skip(f'TODO: model {model_name} is not implemented yet.')


def _field_names(model):
    return {field.name for field in model._meta.get_fields()}


def _pk_value(instance):
    return getattr(instance, 'pk', getattr(instance, 'id', None))


def _fk_kwargs(model, relation_name, instance):
    names = _field_names(model)
    if relation_name in names:
        return {relation_name: instance}
    relation_id_name = f'{relation_name}_id'
    if relation_id_name in names:
        return {relation_id_name: _pk_value(instance)}
    error_message = CRITICAL_RELATIONS.get((model.__name__, relation_name))
    if error_message:
        pytest.fail(error_message)
    pytest.skip(
        f'TODO: relation {relation_name} is missing on model {model.__name__}.'
    )


def _require_user_with_account_type():
    user_model = get_user_model()
    names = _field_names(user_model)
    if 'account_type' not in names:
        pytest.fail('User.account_type is required in MVP')
    return user_model


def _build_user_kwargs(user_model, username, email, account_type, specialization=None):
    kwargs = {
        'username': username,
        'email': email,
        'account_type': account_type,
    }
    names = _field_names(user_model)
    if specialization is not None:
        if 'specialization' in names:
            kwargs['specialization'] = specialization
        elif 'specialization_id' in names:
            kwargs['specialization_id'] = _pk_value(specialization)
    return kwargs


@pytest.fixture
def api_client_class():
    module = pytest.importorskip('rest_framework.test')
    return module.APIClient


@pytest.fixture
def api_client(api_client_class):
    return api_client_class()


@pytest.fixture
def api_request():
    def _request(client, method, path, **kwargs):
        try:
            resolve(path)
        except Resolver404:
            pytest.fail(f'Endpoint is missing from URLConf: {path}')

        request_method = getattr(client, method.lower())
        if method.lower() in {'post', 'patch', 'put'} and 'format' not in kwargs:
            kwargs['format'] = 'json'
        return request_method(path, **kwargs)

    return _request


@pytest.fixture
def field(db):
    field_model = _model_by_name('Field')
    return field_model.objects.create(name=f'Field {uuid.uuid4().hex[:8]}')


@pytest.fixture
def specialization(db, field):
    specialization_model = _model_by_name('Specialization')
    kwargs = {'name': f'Specialization {uuid.uuid4().hex[:8]}'}
    kwargs.update(_fk_kwargs(specialization_model, 'field', field))
    return specialization_model.objects.create(**kwargs)


@pytest.fixture
def skill(db):
    skill_model = _model_by_name('Skill')
    return skill_model.objects.create(name=f'Skill {uuid.uuid4().hex[:8]}')


@pytest.fixture
def owner_password():
    return 'OwnerPass123!'


@pytest.fixture
def participant_password():
    return 'ParticipantPass123!'


@pytest.fixture
def owner(db, specialization, owner_password):
    user_model = _require_user_with_account_type()
    kwargs = _build_user_kwargs(
        user_model=user_model,
        username=f'owner_{uuid.uuid4().hex[:8]}',
        email=f'owner_{uuid.uuid4().hex[:8]}@example.com',
        account_type='owner',
        specialization=specialization,
    )
    return user_model.objects.create_user(password=owner_password, **kwargs)


@pytest.fixture
def participant(db, specialization, participant_password):
    user_model = _require_user_with_account_type()
    kwargs = _build_user_kwargs(
        user_model=user_model,
        username=f'participant_{uuid.uuid4().hex[:8]}',
        email=f'participant_{uuid.uuid4().hex[:8]}@example.com',
        account_type='participant',
        specialization=specialization,
    )
    return user_model.objects.create_user(password=participant_password, **kwargs)


@pytest.fixture
def second_participant(db, specialization, participant_password):
    user_model = _require_user_with_account_type()
    kwargs = _build_user_kwargs(
        user_model=user_model,
        username=f'participant_{uuid.uuid4().hex[:8]}',
        email=f'participant_{uuid.uuid4().hex[:8]}@example.com',
        account_type='participant',
        specialization=specialization,
    )
    return user_model.objects.create_user(password=participant_password, **kwargs)


@pytest.fixture
def owner_client(api_client_class, owner):
    client = api_client_class()
    client.force_authenticate(user=owner)
    return client


@pytest.fixture
def participant_client(api_client_class, participant):
    client = api_client_class()
    client.force_authenticate(user=participant)
    return client


@pytest.fixture
def second_participant_client(api_client_class, second_participant):
    client = api_client_class()
    client.force_authenticate(user=second_participant)
    return client


@pytest.fixture
def project_payload(field):
    return {
        'field_id': _pk_value(field),
        'title': 'TeamLab MVP Project',
        'description': 'Project description',
        'idea': 'Useful idea',
        'benefits': 'Useful benefits',
        'status': 'open',
    }


@pytest.fixture
def role_payload(specialization):
    return {
        'specialization_id': _pk_value(specialization),
        'description': 'Need one participant',
        'capacity': 1,
        'is_open': True,
    }


@pytest.fixture
def project(db, owner, field):
    project_model = _model_by_name('Project')
    kwargs = {
        'title': 'Open Project',
        'description': 'Open project description',
        'idea': 'Open idea',
        'benefits': 'Open benefits',
        'status': 'open',
    }
    kwargs.update(_fk_kwargs(project_model, 'owner', owner))
    kwargs.update(_fk_kwargs(project_model, 'field', field))
    return project_model.objects.create(**kwargs)


@pytest.fixture
def closed_project(db, owner, field):
    project_model = _model_by_name('Project')
    kwargs = {
        'title': 'Closed Project',
        'description': 'Closed project description',
        'idea': 'Closed idea',
        'benefits': 'Closed benefits',
        'status': 'closed',
    }
    kwargs.update(_fk_kwargs(project_model, 'owner', owner))
    kwargs.update(_fk_kwargs(project_model, 'field', field))
    return project_model.objects.create(**kwargs)


@pytest.fixture
def project_role(db, project, specialization):
    project_role_model = _model_by_name('ProjectRole')
    kwargs = {
        'description': 'Open role',
        'capacity': 1,
        'is_open': True,
    }
    kwargs.update(_fk_kwargs(project_role_model, 'project', project))
    kwargs.update(_fk_kwargs(project_role_model, 'specialization', specialization))
    return project_role_model.objects.create(**kwargs)


@pytest.fixture
def closed_project_role(db, project, specialization):
    project_role_model = _model_by_name('ProjectRole')
    kwargs = {
        'description': 'Closed role',
        'capacity': 1,
        'is_open': False,
    }
    kwargs.update(_fk_kwargs(project_role_model, 'project', project))
    kwargs.update(_fk_kwargs(project_role_model, 'specialization', specialization))
    return project_role_model.objects.create(**kwargs)


@pytest.fixture
def role_in_closed_project(db, closed_project, specialization):
    project_role_model = _model_by_name('ProjectRole')
    kwargs = {
        'description': 'Role in closed project',
        'capacity': 1,
        'is_open': True,
    }
    kwargs.update(_fk_kwargs(project_role_model, 'project', closed_project))
    kwargs.update(_fk_kwargs(project_role_model, 'specialization', specialization))
    return project_role_model.objects.create(**kwargs)


@pytest.fixture
def role_interest(db, participant, project_role):
    role_interest_model = _model_by_name('RoleInterest')
    kwargs = {'status': 'pending'}
    kwargs.update(_fk_kwargs(role_interest_model, 'user', participant))
    kwargs.update(_fk_kwargs(role_interest_model, 'project_role', project_role))
    return role_interest_model.objects.create(**kwargs)
