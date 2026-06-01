from typing import Any

from users.models import UserSkill


UserSkillData = dict[str, Any]


def create_user_skills(user, skills_data: list[UserSkillData]) -> None:
    """
    Создать навыки пользователя.

    Args:
        user: Пользователь, к которому привязываются навыки.
        skills_data: Список валидированных данных для UserSkill.
            Каждый словарь ожидается в формате:
            {
                'skill': Skill,
                'level': str,
            }

    Note:
        Функция не открывает transaction.atomic().
        Если создание или замена навыков должно быть атомарным вместе
        с обновлением профиля пользователя, транзакцию нужно открыть
        во внешнем коде.

    """
    UserSkill.objects.bulk_create([
        UserSkill(
            user=user,
            **skill_data
        )
        for skill_data in skills_data
    ])


def replace_user_skills(user, skills_data:list[UserSkillData]) -> None:
  """
    Полностью заменить навыки пользователя.

    Args:
        user: Пользователь, у которого нужно заменить навыки.
        skills_data: Новый список валидированных данных для UserSkill.
            Каждый словарь ожидается в формате:
            {
                'skill': Skill,
                'level': str,
            }

    Note:
        Функция удаляет все старые UserSkill пользователя и создаёт новые.
        Она не открывает transaction.atomic(), поэтому атомарность должен
        обеспечить вызывающий код.

    """
  user.skills.all().delete()
  create_user_skills(user, skills_data)