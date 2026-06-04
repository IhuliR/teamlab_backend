import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from projects.models import (
    Field,
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
    RoleInterest,
    Specialization,
)
from users.models import FavoriteProject, PortfolioWork, Skill


BASE64_IMAGE = (
    'data:image/png;base64,'
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
    'YAAAAAYAAjCB0C8AAAAASUVORK5CYII='
)


def unique(prefix):
    return f'{prefix}_{uuid.uuid4().hex[:8]}'


def pk(instance):
    return instance.pk


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / 'media'


@pytest.fixture
def api_client():
    client = APIClient()
    client.raise_request_exception = False
    return client


@pytest.fixture
def anonymous_client(api_client):
    return api_client


@pytest.fixture
def api_request():
    def _request(client, method, path, **kwargs):
        request_method = getattr(client, method.lower())
        if method.lower() in {'post', 'patch', 'put'} and 'format' not in kwargs:
            kwargs['format'] = 'json'
        return request_method(path, **kwargs)

    return _request


@pytest.fixture
def password():
    return 'StrongPass123!'


@pytest.fixture
def create_user(db, password):
    def _create_user(
        username=None,
        email=None,
        account_type='participant',
        specialization=None,
        **extra,
    ):
        User = get_user_model()
        username = username or unique(account_type)
        email = email or f'{username}@example.com'
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            account_type=account_type,
            specialization=specialization,
            **extra,
        )

    return _create_user


@pytest.fixture
def make_client():
    def _make_client(user):
        client = APIClient()
        client.raise_request_exception = False
        client.force_authenticate(user=user)
        return client

    return _make_client


@pytest.fixture
def field(db):
    return Field.objects.create(name=unique('Development'))


@pytest.fixture
def another_field(db):
    return Field.objects.create(name=unique('Design'))


@pytest.fixture
def featured_field(db):
    return Field.objects.create(
        name=unique('Featured'),
        is_featured=True,
        featured_order=2,
    )


@pytest.fixture
def first_featured_field(db):
    return Field.objects.create(
        name=unique('AlphaFeatured'),
        is_featured=True,
        featured_order=1,
    )


@pytest.fixture
def backend_specialization(db, field):
    return Specialization.objects.create(name='Backend', field=field)


@pytest.fixture
def frontend_specialization(db, field):
    return Specialization.objects.create(name='Frontend', field=field)


@pytest.fixture
def designer_specialization(db, another_field):
    return Specialization.objects.create(name='Designer', field=another_field)


@pytest.fixture
def specialization(backend_specialization):
    return backend_specialization


@pytest.fixture
def python_skill(db):
    return Skill.objects.create(name='Python')


@pytest.fixture
def django_skill(db):
    return Skill.objects.create(name='Django')


@pytest.fixture
def react_skill(db):
    return Skill.objects.create(name='React')


@pytest.fixture
def figma_skill(db):
    return Skill.objects.create(name='Figma')


@pytest.fixture
def skill(python_skill):
    return python_skill


@pytest.fixture
def owner(create_user):
    return create_user(account_type='owner', specialization=None)


@pytest.fixture
def participant_backend_user(create_user, backend_specialization):
    return create_user(
        username=unique('backend'),
        account_type='participant',
        specialization=backend_specialization,
    )


@pytest.fixture
def participant_designer_user(create_user, designer_specialization):
    return create_user(
        username=unique('designer'),
        account_type='participant',
        specialization=designer_specialization,
    )


@pytest.fixture
def participant_member_user(create_user, frontend_specialization):
    return create_user(
        username=unique('member'),
        account_type='participant',
        specialization=frontend_specialization,
    )


@pytest.fixture
def participant(participant_backend_user):
    return participant_backend_user


@pytest.fixture
def second_participant(participant_designer_user):
    return participant_designer_user


@pytest.fixture
def owner_client(make_client, owner):
    return make_client(owner)


@pytest.fixture
def backend_client(make_client, participant_backend_user):
    return make_client(participant_backend_user)


@pytest.fixture
def designer_client(make_client, participant_designer_user):
    return make_client(participant_designer_user)


@pytest.fixture
def member_client(make_client, participant_member_user):
    return make_client(participant_member_user)


@pytest.fixture
def participant_client(backend_client):
    return backend_client


@pytest.fixture
def second_participant_client(designer_client):
    return designer_client


@pytest.fixture
def project(db, owner, field):
    return Project.objects.create(
        owner=owner,
        field=field,
        title=unique('Open Project'),
        description='Project description',
        problem='Project problem',
        status=Project.Status.OPEN,
    )


@pytest.fixture
def another_project(db, owner, another_field):
    return Project.objects.create(
        owner=owner,
        field=another_field,
        title=unique('Another Project'),
        description='Another description',
        problem='Another problem',
        status=Project.Status.OPEN,
    )


@pytest.fixture
def closed_project(db, owner, field):
    return Project.objects.create(
        owner=owner,
        field=field,
        title=unique('Closed Project'),
        description='Closed description',
        problem='Closed problem',
        status=Project.Status.CLOSED,
    )


@pytest.fixture
def featured_project(db, owner, field):
    return Project.objects.create(
        owner=owner,
        field=field,
        title=unique('Featured Project'),
        description='Featured description',
        problem='Featured problem',
        status=Project.Status.OPEN,
        is_featured=True,
        featured_order=1,
    )


@pytest.fixture
def closed_featured_project(db, owner, field):
    return Project.objects.create(
        owner=owner,
        field=field,
        title=unique('Closed Featured Project'),
        description='Closed featured description',
        problem='Closed featured problem',
        status=Project.Status.CLOSED,
        is_featured=True,
        featured_order=0,
    )


@pytest.fixture
def backend_project_role(db, project, backend_specialization):
    return ProjectRole.objects.create(
        project=project,
        specialization=backend_specialization,
        tasks=['Build API'],
        benefits=['Backend practice'],
    )


@pytest.fixture
def frontend_project_role(db, project, frontend_specialization):
    return ProjectRole.objects.create(
        project=project,
        specialization=frontend_specialization,
        tasks=['Build UI'],
        benefits=['Frontend practice'],
    )


@pytest.fixture
def designer_project_role(db, project, designer_specialization):
    return ProjectRole.objects.create(
        project=project,
        specialization=designer_specialization,
        tasks=['Design flows'],
        benefits=['Design practice'],
    )


@pytest.fixture
def project_role(backend_project_role):
    return backend_project_role


@pytest.fixture
def closed_project_role(db, closed_project, backend_specialization):
    return ProjectRole.objects.create(
        project=closed_project,
        specialization=backend_specialization,
        tasks=['Closed task'],
        benefits=['Closed benefit'],
    )


@pytest.fixture
def project_role_skill(db, backend_project_role, python_skill):
    return ProjectRoleSkill.objects.create(
        project_role=backend_project_role,
        skill=python_skill,
        description='Python backend',
        order=1,
    )


@pytest.fixture
def pending_application(db, participant_backend_user, backend_project_role):
    return RoleInterest.objects.create(
        user=participant_backend_user,
        project_role=backend_project_role,
        source=RoleInterest.Source.APPLICATION,
        status=RoleInterest.Status.PENDING,
    )


@pytest.fixture
def pending_invitation(db, participant_designer_user, designer_project_role):
    return RoleInterest.objects.create(
        user=participant_designer_user,
        project_role=designer_project_role,
        source=RoleInterest.Source.INVITATION,
        status=RoleInterest.Status.PENDING,
    )


@pytest.fixture
def accepted_role_interest(db, participant_member_user, frontend_project_role):
    return RoleInterest.objects.create(
        user=participant_member_user,
        project_role=frontend_project_role,
        source=RoleInterest.Source.APPLICATION,
        status=RoleInterest.Status.ACCEPTED,
    )


@pytest.fixture
def role_interest(pending_application):
    return pending_application


@pytest.fixture
def active_membership(db, accepted_role_interest, participant_member_user, frontend_project_role):
    return ProjectMembership.objects.create(
        user=participant_member_user,
        project_role=frontend_project_role,
        role_interest=accepted_role_interest,
        status=ProjectMembership.Status.ACTIVE,
    )


@pytest.fixture
def favorite_project(db, participant_backend_user, project):
    return FavoriteProject.objects.create(
        user=participant_backend_user,
        project=project,
    )


@pytest.fixture
def portfolio_work(db, participant_backend_user):
    return PortfolioWork.objects.create(
        user=participant_backend_user,
        title='Portfolio item',
        task='Task',
        solution='Solution',
        technologies=['Python', 'Django'],
        link='https://example.com/work',
    )


@pytest.fixture
def project_payload(field, backend_specialization, python_skill):
    return {
        'field_id': pk(field),
        'title': 'TeamLab MVP Project',
        'description': 'Project description',
        'problem': 'Project problem',
        'image': BASE64_IMAGE,
        'roles': [
            {
                'specialization_id': pk(backend_specialization),
                'tasks': ['Build REST API'],
                'benefits': ['Real backend practice'],
                'skills': [
                    {
                        'skill_id': pk(python_skill),
                        'description': 'Python backend',
                        'order': 1,
                    }
                ],
            }
        ],
    }


@pytest.fixture
def role_payload(project, designer_specialization, figma_skill):
    return {
        'project_id': pk(project),
        'specialization_id': pk(designer_specialization),
        'tasks': ['Prepare UI kit'],
        'benefits': ['Portfolio case'],
        'skills': [
            {
                'skill_id': pk(figma_skill),
                'description': 'Figma design',
                'order': 1,
            }
        ],
    }


@pytest.fixture
def base64_image():
    return BASE64_IMAGE
