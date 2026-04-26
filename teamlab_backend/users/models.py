from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .constants import (
    MAX_USERNAME_LEN,
    MAX_EMAIL_LEN,
    MIN_INGREDIENT_AMOUNT,
    MAX_HOURS_PER_WEEK,
)
from projects.models import Specialization


class User(AbstractUser):

    class AccountType(models.TextChoices):
        PARTICIPANT = 'participant', 'Participant'
        OWNER = 'owner', 'Owner'
    
    class Level(models.TextChoices):
        JUNIOR = 'junior', 'Junior'
        MIDDLE = 'middle', 'Middle'
        SENIOR = 'senior', 'Senior'

    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices
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
        null=True,
        blank=True,
        verbose_name='Описание'
    )
    email = models.EmailField(
        unique=True,
        max_length=MAX_EMAIL_LEN,
        verbose_name='Почта'
    )
    specialization_id = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Специализация'
    )
    level = models.CharField(
        max_length=20,
        choices=Level.choices
    )
    workload_hours_per_week = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
            MaxValueValidator(MAX_HOURS_PER_WEEK)
        ],
        verbose_name='Количество рабочих часов в неделю'
    )
    work_format = models.CharField(
        verbose_name='Формат работы'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username
