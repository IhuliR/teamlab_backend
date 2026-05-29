from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .constants import (
    MAX_ACCOUNT_TYPE_LEN,
    MAX_CITY_LEN,
    MAX_EMAIL_LEN,
    MAX_HOURS_PER_WEEK,
    MAX_LEVEL_LEN,
    MAX_SKILL_NAME_LEN,
    MAX_SEARCH_STATUS_LEN,
    MAX_USERNAME_LEN,
    MAX_WORK_FORMAT_LEN,
    MIN_HOURS_PER_WEEK,
    MAX_TASK_LEN,
    MAX_SOLUTION_LEN,
    MAX_PROFILE_VISIBILITY_LEN,
    MAX_PORTFOLIO_TITLE_LEN,
    MAX_EMPLOYMENT_TYPE_LEN
)
from .validators import username_validator


class User(AbstractUser):

    class AccountType(models.TextChoices):
        PARTICIPANT = 'participant', 'Участник'
        OWNER = 'owner', 'Владелец'
    
    class Level(models.TextChoices):
        JUNIOR = 'junior', 'Базовый'
        MIDDLE = 'middle', 'Средний'
        SENIOR = 'senior', 'Продвинутый'

    class WorkFormat(models.TextChoices):
        REMOTE = 'remote', 'Удалённо'
        HYBRID = 'hybrid', 'Гибрид'

    class ProfileVisibility(models.TextChoices):
        PUBLIC = 'public', 'Публичный'
        MATCHED_ONLY = 'matched_only', 'Только метчи'
        HIDDEN = 'hidden', 'Скрытый'

    class EmploymentType(models.TextChoices):
        COMBINED = 'combined', 'Совмещаю'
        FULL_TIME = 'full_time', 'Полная занятость'
        PART_TIME = 'part_time', 'Частичная занятость'
    
    class SearchStatus(models.TextChoices):
        LOOKING_FOR_TEAM = 'looking_for_team', 'Ищу команду'
        LOOKING_FOR_MEMBERS = 'looking_for_members', 'Ищу участников'
        NOT_LOOKING = 'not_looking', 'Не ищу'

    username = models.CharField(
        max_length=MAX_USERNAME_LEN,
        unique=True,
        validators=[username_validator],
        verbose_name='Юзернейм'
    )
    email = models.EmailField(
        unique=True,
        max_length=MAX_EMAIL_LEN,
        verbose_name='Почта'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    account_type = models.CharField(
        max_length=MAX_ACCOUNT_TYPE_LEN,
        choices=AccountType.choices,
        verbose_name='Тип аккаунта'
    )
    specialization = models.ForeignKey(
        'projects.Specialization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Специализация'
    )
    level = models.CharField(
        max_length=MAX_LEVEL_LEN,
        choices=Level.choices,
        null=True,
        blank=True,
        verbose_name='Уровень'
    )
    workload_hours_per_week = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_HOURS_PER_WEEK),
            MaxValueValidator(MAX_HOURS_PER_WEEK)
        ],
        null=True,
        blank=True,
        verbose_name='Количество рабочих часов в неделю'
    )
    work_format = models.CharField(
        max_length=MAX_WORK_FORMAT_LEN,
        choices=WorkFormat.choices,
        null=True,
        blank=True,
        verbose_name='Формат работы'
    )
    employment_type = models.CharField(
        max_length=MAX_EMPLOYMENT_TYPE_LEN,
        choices=EmploymentType.choices,
        null=True,
        blank=True,
        verbose_name='Тип занятости'
    )
    search_status = models.CharField(
        max_length=MAX_SEARCH_STATUS_LEN,
        choices=SearchStatus.choices,
        null=True,
        blank=True,
        verbose_name='Статус поиска'
    )
    profile_visibility = models.CharField(
        max_length=MAX_PROFILE_VISIBILITY_LEN,
        choices=ProfileVisibility.choices,
        default=ProfileVisibility.PUBLIC,
        verbose_name='Видимость профиля'
    )
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name='Уведомления включены'
    )
    city = models.CharField(
        max_length=MAX_CITY_LEN,
        blank=True,
        verbose_name='Город'
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    social_links = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Социальные сети'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Skill(models.Model):
    name = models.CharField(
        max_length=MAX_SKILL_NAME_LEN,
        unique=True,
        verbose_name='Название'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'
        ordering = ('name',)
    
    def __str__(self):
        return self.name


class UserSkill(models.Model):

    class Level(models.TextChoices):
        BASIC = 'basic', 'Basic'
        MIDDLE = 'middle', 'Middle'
        ADVANCED = 'advanced', 'Advanced'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name='Пользователь'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='Навык'
    )
    level = models.CharField(
        choices=Level.choices,
        max_length=MAX_LEVEL_LEN,
        verbose_name='Уровень'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Навыки пользователя'
        verbose_name_plural = 'Навыки пользователей'
        ordering = ('user', 'skill')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'skill'],
                name='unique_user_skill'
            ),
        ]
    
    def __str__(self):
        return f'{self.user} - {self.skill}'


class PortfolioWork(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolio_works',
        verbose_name='Пользователь'
    )
    title = models.CharField(
        max_length=MAX_PORTFOLIO_TITLE_LEN,
        verbose_name='Название проекта портфолио'
    )
    task = models.TextField(
        max_length=MAX_TASK_LEN,
        null=True,
        blank=True,
        verbose_name='Задача'
    )
    solution = models.TextField(
        max_length=MAX_SOLUTION_LEN,
        null=True,
        blank=True,
        verbose_name='Решение'
    )
    image = models.ImageField(
        upload_to='portfolio_images/',
        null=True,
        blank=True,
        verbose_name='Изображение работы портфолио'
    )
    technologies = models.JSONField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Работа портфолио'
        verbose_name_plural = 'Работы портфолио'
        ordering = ('-created_at',)

    def __str__(self):
        return self.title


class FavoriteProject(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_projects',
        verbose_name='Пользователь'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Проект'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранный проект'
        verbose_name_plural = 'Избранные проекты'
        ordering = ('user', 'project')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'project'],
                name='unique_user_favorite_project',
            ),
        ]

    def __str__(self):
        return f'{self.user} — {self.project}'

    def clean(self):
        super().clean()

        if (
            self.user_id
            and self.user.account_type != User.AccountType.PARTICIPANT
        ):
            raise ValidationError(
                'Добавлять проекты в избранное могут только участники.'
            )