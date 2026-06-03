from typing import Any

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from projects.models import (
    Project,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
    RoleInterest
)


User = get_user_model()

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
    

def validate_project_role_can_be_deleted(project_role, actor) -> None:
    """Проверить, что роль проекта можно удалить."""

    if project_role.project.owner_id != actor.id:
        raise PermissionDenied(
            'Удалить роль может только владелец.'
        )

    if ProjectMembership.objects.filter(
        project_role_id=project_role.id,
        status=ProjectMembership.Status.ACTIVE,
    ).exists():
        raise ValidationError({
            'project_role_id': (
                'Нельзя удалить роль, пока по ней есть активные участники.'
            )
        })

    if RoleInterest.objects.filter(
        project_role=project_role,
        status=RoleInterest.Status.PENDING,
    ).exists():
        raise ValidationError(
            'Нельзя удалить роль, пока по ней есть необработанные '
            'заявки или приглашения.'
        )


def get_matching_project_role(project, user):
    """Найти роль проекта, соотретствующую специализации пользователя."""
    if user.specialization_id is None:
        raise ValidationError({
            'specialization_id': (
                'Для отклика или приглашения у пользователя должна быть '
                'указана специализация.'
            )
        })
    
    roles = project.roles.filter(
        specialization=user.specialization,
    )

    if not roles.exists():
        raise ValidationError({
            'project_id': (
                'В проекте нет роли, '
                'соответствующей специализации пользователя'
            )
        })
    
    if roles.count() > 1:
        raise ValidationError({
            'project_id': (
                'В проекте найдено несколько ролей с этой специализацией. '
                'Нужно исправить роли проекта.'
            )
        })
    
    return roles.first()


def create_project_application(project, user):
    """Создать заявку участника на проект."""
    if user.account_type != User.AccountType.PARTICIPANT:
        raise PermissionDenied(
            'Только участник может откликаться на проекты.'
        )

    if project.owner_id == user.id:
        raise ValidationError({
            'project_id': 'Нельзя откликнуться на собственный проект.'
        })
    
    if project.status != project.Status.OPEN:
        raise ValidationError({
            'project_id': 'Откликаться можно только на открытые проекты.'
        })
    
    project_role = get_matching_project_role(project, user)

    if ProjectMembership.objects.filter(
        user=user,
        project_role__project=project,
        status=ProjectMembership.Status.ACTIVE
    ).exists():
        raise ValidationError({
            'project_id': 'Вы уже участвуете в этом проекте.'
        })
    
    if RoleInterest.objects.filter(
        user=user,
        project_role=project_role
    ).exists():
        raise ValidationError({
            'project_role_id': (
                'По этой роли уже есть '
                'история взаимодействия с пользователем.'
                'Повторные заявки и приглашения в MVP не поддерживаются.'
            )
        })
    
    try:
        with transaction.atomic():
            return RoleInterest.objects.create(
                user=user,
                project_role=project_role,
                source=RoleInterest.Source.APPLICATION,
                status=RoleInterest.Status.PENDING,
            )
    except IntegrityError:
        raise ValidationError({
            'project_role_id': (
                'Отклик на эту роль уже существует.'
            )
        })


def create_project_invitation(project, actor, invited_user):
    """Создать приглашение пользователя в проект."""
    if actor.account_type != User.AccountType.OWNER:
        raise PermissionDenied(
            'Только владелец проекта может приглашать участников.'
        )

    if project.owner_id != actor.id:
        raise PermissionDenied(
            'Приглашать участников может только владелец этого проекта.'
        )

    if invited_user.account_type != User.AccountType.PARTICIPANT:
        raise ValidationError({
            'user_id': 'Пригласить можно только пользователя-участника.'
        })

    if project.status != project.Status.OPEN:
        raise ValidationError({
            'project_id': 'Приглашать можно только в открытый проект.'
        })

    project_role = get_matching_project_role(project, invited_user)

    if ProjectMembership.objects.filter(
        user=invited_user,
        project_role__project=project,
        status=ProjectMembership.Status.ACTIVE,
    ).exists():
        raise ValidationError({
            'user_id': 'Пользователь уже участвует в этом проекте.'
        })

    if RoleInterest.objects.filter(
        user=invited_user,
        project_role__project=project,
        status=RoleInterest.Status.PENDING,
    ).exists():
        raise ValidationError({
            'user_id': (
                'У пользователя уже есть необработанная заявка или '
                'приглашение по этому проекту.'
            )
        })

    if RoleInterest.objects.filter(
        user=invited_user,
        project_role=project_role,
    ).exists():
        raise ValidationError({
            'project_id': (
                'По этому проекту уже есть история взаимодействия. '
                'Повторные заявки и приглашения в MVP не поддерживаются.'
            )
        })

    try:
        with transaction.atomic():
            return RoleInterest.objects.create(
                user=invited_user,
                project_role=project_role,
                source=RoleInterest.Source.INVITATION,
                status=RoleInterest.Status.PENDING,
            )
    except IntegrityError:
        raise ValidationError({
            'project_role_id': (
                'Приглашение или заявка на эту роль уже существует.'
            )
        })


def validate_role_interest_can_be_processed(interest, actor) -> None:
    """Проверить, что пользователь может обработать заявку/приглашение."""

    if interest.status != RoleInterest.Status.PENDING:
        raise ValidationError(
            'Можно обработать только необработанную заявку или приглашение.'
        )

    if interest.source == RoleInterest.Source.APPLICATION:
        if interest.project_role.project.owner_id != actor.id:
            raise PermissionDenied(
                'Принять или отклонить заявку может только владелец проекта.'
            )
        return

    if interest.source == RoleInterest.Source.INVITATION:
        if interest.user_id != actor.id:
            raise PermissionDenied(
                'Принять или отклонить приглашение может '
                'только приглашённый пользователь.'
            )
        return

    raise ValidationError(
        'Некорректный источник заявки или приглашения.'
    )


def accept_role_interest(interest, actor):
    """Принять заявку или приглашение и создать участие в проекте."""

    validate_role_interest_can_be_processed(
        interest=interest,
        actor=actor,
    )

    try:
        with transaction.atomic():
            if ProjectMembership.objects.filter(
                user=interest.user,
                project_role__project=interest.project_role.project,
                status=ProjectMembership.Status.ACTIVE,
            ).exists():
                raise ValidationError(
                    'Пользователь уже участвует в этом проекте.'
                )

            now = timezone.now()

            interest.status = RoleInterest.Status.ACCEPTED
            interest.reviewed_at = now
            interest.save(update_fields=(
                'status',
                'reviewed_at',
                'updated_at',
            ))

            ProjectMembership.objects.create(
                user=interest.user,
                project_role=interest.project_role,
                role_interest=interest,
                status=ProjectMembership.Status.ACTIVE,
                joined_at=now,
            )

    except IntegrityError:
        raise ValidationError(
            'Участие по этой заявке или приглашению уже существует.'
        )

    return interest


def reject_role_interest(interest, actor):
    """Отклонить заявку или приглашение."""

    validate_role_interest_can_be_processed(
        interest=interest,
        actor=actor,
    )

    interest.status = RoleInterest.Status.REJECTED
    interest.reviewed_at = timezone.now()
    interest.save(update_fields=(
        'status',
        'reviewed_at',
        'updated_at',
    ))

    return interest


def remove_project_membership(membership, actor):
    """Исключить участника из проекта."""
    if membership.project_role.project.owner_id != actor.id:
        raise PermissionDenied(
            'Исключить участника может только владелец проекта.'
        )

    if membership.status != ProjectMembership.Status.ACTIVE:
        raise ValidationError(
            'Можно исключить только активного участника.'
        )

    membership.status = ProjectMembership.Status.REMOVED
    membership.ended_at = timezone.now()
    membership.save(update_fields=('status', 'ended_at', 'updated_at'))

    return membership


def leave_project_membership(membership, actor):
    """Покинуть проект."""
    if membership.user_id != actor.id:
        raise PermissionDenied(
            'Покинуть проект может только сам участник.'
        )

    if membership.status != ProjectMembership.Status.ACTIVE:
        raise ValidationError(
            'Можно покинуть только активное участие.'
        )

    membership.status = ProjectMembership.Status.LEFT
    membership.ended_at = timezone.now()
    membership.save(update_fields=('status', 'ended_at', 'updated_at'))

    return membership
