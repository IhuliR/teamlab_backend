import boto3
import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from .models import ImageUpload
from projects.models import Project
from users.models import PortfolioWork


def generate_upload_url(
    key: str,
    content_type: str,
    max_size: int,
) -> dict:
    options = settings.STORAGES['media_s3']['OPTIONS']
    s3 = boto3.client(
        's3',
        endpoint_url=options['endpoint_url'],
        region_name=options['region_name'],
    )

    return s3.generate_presigned_post(
        Bucket=options['bucket_name'],
        Key=key,
        Fields={
            'Content-Type': content_type,
        },
        Conditions=[
            {'Content-Type': content_type},
            ['content-length-range', 1, max_size],
        ],
        ExpiresIn=settings.IMAGE_PRESIGN_TTL_SECONDS,
    )


def create_image_upload(*, user, validated_data):
    kind = validated_data['kind']
    target_id = validated_data.get('target_id')

    target_fields = {
        'project': None,
        'portfolio_work': None,
    }

    if kind == ImageUpload.Kind.PROJECT_IMAGE:
        project = Project.objects.filter(pk=target_id).first()

        if project is None:
            raise NotFound('Проект не найден.')
        
        if project.owner_id != user.pk:
            raise PermissionDenied('Нет прав на изменение проекта.')
        
        target_fields['project'] = project
    
    elif kind == ImageUpload.Kind.PORTFOLIO_IMAGE:
        work = PortfolioWork.objects.filter(pk=target_id).first()

        if work is None:
            raise NotFound('Работа портфолио не найдена.')
        
        if work.user_id != user.pk:
            raise PermissionDenied('Нет прав на изменение портфолио.')

        target_fields['portfolio_work'] = work
    
    upload_id = uuid.uuid4()
    temporary_key = f'temporary/{upload_id}/image'

    presigned = generate_upload_url(
        key=temporary_key,
        content_type=validated_data['content_type'],
        max_size=settings.IMAGE_UPLOAD_LIMITS[kind],
    )

    upload = ImageUpload.objects.create(
        id=upload_id,
        owner=user,
        kind=kind,
        temporary_key=temporary_key,
        declared_size=validated_data['size_bytes'],
        declared_content_type=validated_data['content_type'],
        expires_at=timezone.now() + timedelta(
            seconds=settings.IMAGE_PRESIGN_TTL_SECONDS,
        ),
        **target_fields,
    )
    return upload, presigned
