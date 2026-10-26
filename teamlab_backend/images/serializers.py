from django.conf import settings
from rest_framework import serializers

from .models import ImageUpload


class ImageUploadCreateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(
        choices=ImageUpload.Kind.choices,
    )
    target_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    content_type = serializers.ChoiceField(
        choices=(
            'image/jpeg',
            'image/png',
            'image/webp',
        ),
    )
    size_bytes = serializers.IntegerField(
        min_value=1,
    )
    def validate(self, attrs):
        kind = attrs['kind']
        target_id = attrs.get('target_id')

        if kind == ImageUpload.Kind.USER_AVATAR:
            if target_id is not None:
                raise serializers.ValidationError({
                    'target_id': 'Для аватара target_id не нужен.',
                })
        elif target_id is None:
            raise serializers.ValidationError({
                'target_id': 'Укажите ID проекта или работы партфолио.',
            })

        max_size = settings.IMAGE_UPLOAD_LIMITS[kind]

        if attrs['size_bytes'] > max_size:
            raise serializers.ValidationError({
                'size_bytes': 'Размер изображения превышает лимит.'
            })

        return attrs
