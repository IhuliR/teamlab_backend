from typing import Any

from django.db import transaction

from projects.models import Project, ProjectRole, ProjectRoleSkill
from users.models import User

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
        owner: User,
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
