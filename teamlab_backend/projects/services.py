from typing import Any

from projects.models import ProjectRole, ProjectRoleSkill


ProjectRoleSkillData = dict[str, Any]


def create_project_role_skills(
    project_role: ProjectRole,
    skills_data: list[ProjectRoleSkillData],
) -> None:
    """Создать требования к навыкам для роли проекта.

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
    """Полностью заменить требования к навыкам для роли проекта.

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
