from typing import Any

from django.db import transaction
from rest_framework.exceptions import ValidationError

from projects.models import (
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
    RoleInterest
)

ProjectRoleSkillData = dict[str, Any]
ProjectRoleData = dict[str, Any]
ProjectData = dict[str, Any]


def create_project_role_skills(
    project_role: ProjectRole,
    skills_data: list[ProjectRoleSkillData],
) -> None:
    """
    Создать требования к навыкам для роли проекта.

    Args:
        project_role: Роль проекта, к которой привязываются требования.
        skills_data: Список валидированных данных для ProjectRoleSkill.
            Каждый словарь ожидается в формате:
            {
                'skill': Skill,
                'description': str,
                'order': int,
            }

    Note:
        Функция не открывает transaction.atomic().
        Если создание ProjectRole и ProjectRoleSkill должно быть атомарным,
        транзакцию нужно открыть во внешнем коде.

    """
    ProjectRoleSkill.objects.bulk_create([
        ProjectRoleSkill(
            project_role=project_role,
            **skill_data,
        )
        for skill_data in skills_data
    ])


def replace_project_role_skills(
    project_role: ProjectRole,
    skills_data: list[ProjectRoleSkillData],
) -> None:
    """
    Полностью заменить требования к навыкам для роли проекта.

    Args:
        project_role: Роль проекта, у которой нужно заменить требования.
        skills_data: Новый список валидированных данных для ProjectRoleSkill.
            Каждый словарь ожидается в формате:
            {
                'skill': Skill,
                'description': str,
                'order': int,
            }

    Note:
        Функция удаляет все старые ProjectRoleSkill для роли и создаёт новые.
        Она не открывает transaction.atomic(), поэтому атомарность должен
        обеспечить вызывающий код.

    """
    project_role.skill_requirements.all().delete()
    create_project_role_skills(project_role, skills_data)


def create_project_with_roles(
        owner,
        project_data: ProjectData,
        roles_data: list[ProjectRoleData],
) -> Project:
    """
    Создать проект вместе с ролями и требованиями к навыкам.

    Args:
        owner: Пользователь-владелец создаваемого проекта.
        project_data: Валидированные данные для создания Project.
            Ожидается формат:
            {
                'field': Field,
                'title': str,
                'description': str,
                'problem': str,
                'image': ImageFile,
            }
        roles_data: Список валидированных данных для ProjectRole.
            Каждый словарь ожидается в формате:
            {
                'specialization': Specialization,
                'tasks': list[str],
                'benefits': list[str],
                'skills': [
                    {
                        'skill': Skill,
                        'description': str,
                        'order': int,
                    },
                    ...
                ],
            }

    Returns:
        Созданный объект Project.

    Note:
        Эта функция выполняет цельный бизнес-сценарий:
        создание Project, связанных ProjectRole и ProjectRoleSkill.

        В отличие от маленьких helper-функций для создания/замены навыков,
        здесь transaction.atomic() должен открываться внутри функции.
        Это защищает данные от частичного сохранения: если создание любой роли
        или требования к навыку завершится ошибкой, проект и все уже созданные
        связанные объекты будут откатаны целиком.

    """
    with transaction.atomic():
        project = Project.objects.create(
            owner=owner,
            **project_data,
        )

        for role_data in roles_data:
            skills_data = role_data.pop('skills')

            role = ProjectRole.objects.create(
                project=project,
                **role_data,
            )

            create_project_role_skills(role, skills_data)
        
        return project


def find_matching_project_role(user, project: Project) -> ProjectRole | None:
    """
    Найти открытую роль проекта, подходящую пользователю по специализации.

    Args:
        user: Пользователь, для которого ищется роль.
        project: Проект, в котором нужно найти подходящую роль.

    Returns:
        ProjectRole, если в проекте есть открытая роль с той же
        специализацией, что у пользователя. Иначе None.

    Note:
        Функция не создаёт заявки и не проверяет права доступа.
        Она только находит подходящую ProjectRole.
    """
    if not user.specialization_id:
        return None

    return ProjectRole.objects.filter(
        project=project,
        specialization_id=user.specialization_id,
    ).order_by('id').first()


def apply_to_project(user, project):
    role = find_matching_project_role(user=user, project=project)

    if role is None:
        raise ValidationError(
            'В проекте нет открытой роли для вашей специализации.'
        )

    interest = RoleInterest.objects.filter(
        user=user,
        project_role=role,
    ).first()

    if interest and interest.status == RoleInterest.Status.PENDING:
        if interest.source == RoleInterest.Source.INVITATION:
            raise ValidationError(
                'У вас уже есть приглашение в этот проект. '
                'Примите или отклоните его.'
            )

        raise ValidationError(
            'Заявка уже отправлена.'
        )
    

def validate_project_role_can_be_deleted(project_role) -> None:
    """Проверить, что роль проекта можно удалить."""

    if ProjectMembership.objects.filter(
        project_role=project_role,
        status=ProjectMembership.Status.ACTIVE,
    ).exists():
        raise ValidationError(
            'Нельзя удалить роль, пока по ней есть активные участники.'
        )

    if RoleInterest.objects.filter(
        project_role=project_role,
        status=RoleInterest.Status.PENDING,
    ).exists():
        raise ValidationError(
            'Нельзя удалить роль, пока по ней есть необработанные '
            'заявки или приглашения.'
        )
