from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from projects.models import Specialization
from .constants import (
    MAX_ACCOUNT_TYPE_LEN,
    MAX_CITY_LEN,
    MAX_EMAIL_LEN,
    MAX_HOURS_PER_WEEK,
    MAX_LEVEL_LEN,
    MAX_SKILL_NAME_LEN,
    MAX_USERNAME_LEN,
    MAX_WORK_FORMAT_LEN,
    MIN_HOURS_PER_WEEK,
)


class User(AbstractUser):

    class AccountType(models.TextChoices):
        PARTICIPANT = 'participant', 'Participant'
        OWNER = 'owner', 'Owner'
    
    class Level(models.TextChoices):
        JUNIOR = 'junior', 'Junior'
        MIDDLE = 'middle', 'Middle'
        SENIOR = 'senior', 'Senior'

    class WorkFormat(models.TextChoices):
        REMOTE = 'remote', 'Remote'
        HYBRID = 'hybrid', 'Hybrid'
    
    account_type = models.CharField(
        max_length=MAX_ACCOUNT_TYPE_LEN,
        choices=AccountType.choices,
        verbose_name='Тип аккаунта'
    )
    username = models.CharField(
        max_length=MAX_USERNAME_LEN,
        unique=True,
        verbose_name='Юзернейм'
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    email = models.EmailField(
        unique=True,
        max_length=MAX_EMAIL_LEN,
        verbose_name='Почта'
    )
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Специализация'
    )
    level = models.CharField(
        max_length=MAX_LEVEL_LEN,
        choices=Level.choices,
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
        blank=True,
        verbose_name='Формат работы'
    )
    city = models.CharField(
        max_length=MAX_CITY_LEN,
        blank=True,
        verbose_name='Город'
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
        constraints
    
    def __str__(self):
        return self.name