import re

from django.core.exceptions import ValidationError


USERNAME_RE = re.compile(r'^[A-Za-z0-9_@.+-]+\Z')


def username_validator(value):
    """
    Валидация для username.
    Разрешает только латинские буквы, цифры и символы: _ @ . + -
    """
    if not USERNAME_RE.match(value):
        invalid_chars = re.sub(r'[A-Za-z0-9_@.+-]', '', value)
        invalid_unique = ''.join(sorted(set(invalid_chars)))

        raise ValidationError(
            f'Использование {invalid_unique} в username недопустимо.'
        )

    return value
