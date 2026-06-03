from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .constants import (
    DEFAULT_ROLE_ORDER,
    SPECIALIZATION_NAME_MAX_LEN,
    FIELD_NAME_MAX_LEN,
    PROJECT_TITLE_MAX_LEN,
    MAX_STATUS_LEN,
    MAX_SOURCE_LEN
)


class Field(models.Model):
    name = models.CharField(
        max_length=FIELD_NAME_MAX_LEN,
        unique=True,
        verbose_name='Название'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Показывать на главной',
    )
    featured_order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Порядок на главной',
    )

    class Meta:
        verbose_name = 'Область'
        verbose_name_plural = 'Области'
    
    def __str__(self):
        return self.name


class Specialization(models.Model):
    name = models.CharField(
        max_length=SPECIALIZATION_NAME_MAX_LEN,
        verbose_name='Название'
    )
    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name='specializations',
        verbose_name='Область'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
        constraints = [
            models.UniqueConstraint(
                fields=['field', 'name'],
                name='unique_specialization_per_field',
            )
        ]
    
    def __str__(self):
        return self.name


class Project(models.Model):

    class Status(models.TextChoices):
        OPEN = 'open', 'открыт'
        CLOSED = 'closed', 'закрыт'
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        verbose_name='Владелец'
    )
    field = models.ForeignKey(
        Field,
        on_delete=models.PROTECT,
        related_name='projects',
        verbose_name='Область'
    )
    title = models.CharField(
        max_length=PROJECT_TITLE_MAX_LEN,
        verbose_name='Название'
    )
    description = models.TextField(
        verbose_name='Суть проекта'
    )
    problem = models.TextField(
        null=True,
        blank=True,
        verbose_name='Проблема'
    )
    image = models.ImageField(
        upload_to='projects/',
        null=True,
        blank=True,
        verbose_name='Изображение'
    )
    status = models.CharField(
        max_length=MAX_STATUS_LEN,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name='Статус'
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Показывать в подборке',
    )
    featured_order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Порядок на главной',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ('title',)
    
    def __str__(self):
        return self.title


class ProjectRole(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='roles',
        verbose_name='Проект'
    )
    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.PROTECT,
        related_name='project_roles',
        verbose_name='Специализация'
    )
    tasks = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Задачи роли',
    )
    benefits = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Что получите'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Роль в проекте'
        verbose_name_plural = 'Роли в проекте'
        ordering = ('project', 'specialization')
        constraints = [
            models.UniqueConstraint(
                fields=('project', 'specialization'),
                name='unique_project_role_specialization',
            ),
        ]
    
    def __str__(self):
        return f'{self.project} - {self.specialization}'


class ProjectRoleSkill(models.Model):
    project_role = models.ForeignKey(
        ProjectRole,
        on_delete=models.CASCADE,
        related_name='skill_requirements',
        verbose_name='Роль проекта',
    )
    skill = models.ForeignKey(
        'users.Skill',
        on_delete=models.PROTECT,
        related_name='project_role_requirements',
        verbose_name='Навык'
    )
    description = models.TextField(
        verbose_name='Описание требования'
    )
    order = models.PositiveSmallIntegerField(
        default=DEFAULT_ROLE_ORDER
    )

    class Meta:
        verbose_name = 'Навык роли проекта'
        verbose_name_plural = 'Навыки роли проекта'
        ordering = ('project_role', 'order')
        constraints = [
            models.UniqueConstraint(
                fields=['project_role', 'skill'],
                name='unique_project_role_skill'
            ),
            models.UniqueConstraint(
                fields=['project_role', 'order'],
                name='unique_project_role_skill_order',
            ),
        ]
    
    def __str__(self):
        return f'{self.project_role} - {self.skill}'


class RoleInterest(models.Model):

    class Source(models.TextChoices):
        APPLICATION = 'application', 'Заявка'
        INVITATION = 'invitation', 'Приглашение'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        ACCEPTED = 'accepted', 'Принято' 
        REJECTED = 'rejected', 'Отклонено'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='role_interests',
        verbose_name='Пользователь'
    )
    project_role = models.ForeignKey(
        ProjectRole,
        on_delete=models.CASCADE,
        related_name='interests',
        verbose_name='Роль проекта'
    )
    source = models.CharField(
        max_length=MAX_SOURCE_LEN,
        choices=Source.choices,
        verbose_name='Источник'
    )
    status = models.CharField(
        max_length=MAX_STATUS_LEN,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата рассмотрения'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заявка на роль'
        verbose_name_plural = 'Заявки на роль'
        ordering = ('user', 'project_role')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'project_role'],
                name='unique_user_project_role_interest',
            )
        ]
    
    def __str__(self):
        return f'{self.source}: {self.user} - {self.project_role}'

class ProjectMembership(models.Model):

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активен'
        LEFT = 'left', 'Вышел'
        REMOVED = 'removed', 'Исключён'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships',
        verbose_name='Пользователь'
    )
    project_role = models.ForeignKey(
        ProjectRole,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Роль проекта'
    )
    role_interest = models.OneToOneField(
        RoleInterest,
        on_delete=models.PROTECT,
        related_name='membership',
        verbose_name='Заявка/приглашение'
    )
    status = models.CharField(
        max_length=MAX_STATUS_LEN,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус участия'
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата вступления'
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения участия'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Участие в проекте'
        verbose_name_plural = 'Участия в проекте'
        ordering = ('user', 'project_role')
        constraints = [
            models.UniqueConstraint(
                fields=['project_role'],
                condition=models.Q(status='active'),
                name='unique_active_membership_per_project_role'
            )
        ]
    
    def __str__(self):
        return f'{self.user} - {self.project_role}: {self.status}'
    
    def clean(self):
        super().clean()

        if not self.role_interest_id:
            return
    
        if self.role_interest.status != RoleInterest.Status.ACCEPTED:
            raise ValidationError(
                'Участие можно создать только из принятой заявки '
                'или приглашения.'
            )
        
        if self.user_id and self.role_interest.user_id != self.user_id:
            raise ValidationError(
                'Пользователь участия должен совпадать с пользователем заявки.'
            )
        
        if (
            self.project_role_id
            and self.role_interest.project_role_id != self.project_role_id
        ):
            raise ValidationError(
                'Роль участия должна совпадать с ролью заявки.'
            )
