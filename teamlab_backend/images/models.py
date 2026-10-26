import uuid

from django.conf import settings
from django.db import models

from .constants import (
    MAX_KIND_LEN, MAX_STATUS_LEN,
    MAX_TEMPORARY_KEY_LEN,
    MAX_CONTENT_TYPE_LEN,
    MAX_ETAG_LEN,
    MAX_ERROR_CODE_LEN,
    MAX_ERROR_MESSAGE_LEN,
)


class ImageUpload(models.Model):

    class Kind(models.TextChoices):
        USER_AVATAR = 'user_avatar', 'аватар'
        PROJECT_IMAGE = 'project_image', 'изображение проекта'
        PORTFOLIO_IMAGE = 'portfolio_image', 'изображение портфолио'

    class Status(models.TextChoices):
        AWAITING_UPLOAD = 'awaiting_upload', 'Ожидает загрузки'
        QUEUED = 'queued', 'В очереди'
        PROCESSING = 'processing', 'Обрабатывается'
        READY = 'ready', 'Готово'
        FAILED = 'failed', 'Ошибка'
        EXPIRED = 'expired', 'Истекло'
        SUPERSEDED = 'superseded', 'Заменено новой загрузкой'


    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_images',
        verbose_name='Пользователь, инициировавший загрузку',
    )
    kind = models.CharField(
        max_length=MAX_KIND_LEN,
        choices=Kind.choices,
        verbose_name='Тип',
    )
    status = models.CharField(
        max_length=MAX_STATUS_LEN,
        choices=Status.choices,
        default=Status.AWAITING_UPLOAD,
        verbose_name='Статус',
    )
    temporary_key = models.CharField(
        max_length=MAX_TEMPORARY_KEY_LEN,
        unique=True,
        verbose_name='Временный ключ объекта',
    )
    expires_at = models.DateTimeField()
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='image_uploads',
        verbose_name='Проект',
    )
    portfolio_work = models.ForeignKey(
        'users.PortfolioWork',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='image_uploads',
        verbose_name='Работа в портфолио',
    )
    declared_size = models.PositiveBigIntegerField(
        verbose_name='Размер, заявленный клиентом',
    )
    declared_content_type = models.CharField(
        max_length=MAX_CONTENT_TYPE_LEN,
        verbose_name='MIME-тип, заявленный клиентом',
    )
    actual_size = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='Размер, полученный от S3',
    )
    actual_content_type = models.CharField(
        max_length=MAX_CONTENT_TYPE_LEN,
        null=True,
        blank=True,
        verbose_name='MIME-тип, полученный от S3',
    )
    etag = models.CharField(
        max_length=MAX_ETAG_LEN,
        null=True,
        blank=True,
        verbose_name='ETag объекта S3',
    )
    final_key = models.CharField(
        max_length=MAX_TEMPORARY_KEY_LEN,
        null=True,
        blank=True,
        verbose_name='Ключ готового изображения в S3',
    )
    thumbnail_key = models.CharField(
        max_length=MAX_TEMPORARY_KEY_LEN,
        null=True,
        blank=True,
        verbose_name='Ключ миниатюры в S3',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения обработки',
    )
    error_code = models.CharField(
        max_length=MAX_ERROR_CODE_LEN,
        null=True,
        blank=True,
        verbose_name='Код ошибки обработки',
    )
    generation = models.PositiveBigIntegerField(
        default=0,
        verbose_name='Поколение загрузки',
    )
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество попыток обработки',
    )
    next_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время следующей попытки',
    )
    processing_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время начала обработки',
    )
    reserved_bytes = models.PositiveBigIntegerField(
        default=0,
        verbose_name='Зарезервированный объём в байтах',
    )
    error_message = models.CharField(
        max_length=MAX_ERROR_MESSAGE_LEN,
        blank=True,
        default='',
        verbose_name='Описание ошибки',
    )

    class Meta:
        verbose_name = 'Загружаемое изображение'
        verbose_name_plural = 'Загружаемые изображения'
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(kind='user_avatar')
                        & models.Q(project__isnull=True)
                        & models.Q(portfolio_work__isnull=True)
                    )
                    | (
                        models.Q(kind='project_image')
                        & models.Q(project__isnull=False)
                        & models.Q(portfolio_work__isnull=True)
                    )
                    | (
                        models.Q(kind='portfolio_image')
                        & models.Q(project__isnull=True)
                        & models.Q(portfolio_work__isnull=False)
                    )
                ),
                name='image_upload_valid_target'
            )
        ]

    def __str__(self):
        return (
            f'Загружаемое изображение id: {self.id}, '
            f'тип: {self.kind}, статус: {self.status}'
        )
