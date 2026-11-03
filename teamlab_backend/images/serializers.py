from django.conf import settings
from rest_framework import serializers

from .models import ImageUpload
from .services import get_entity_image_url, get_image_url


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


class ImageUploadStatusSerializer(serializers.ModelSerializer):
    upload_id = serializers.UUIDField(source='id', read_only=True)
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageUpload
        fields = (
            'upload_id',
            'kind',
            'status',
            'image_url',
            'thumbnail_url',
            'error_code',
            'error_message',
        )
        read_only_fields = fields

    def get_image_url(self, obj):
        if obj.status not in (
            ImageUpload.Status.READY,
            ImageUpload.Status.ATTACHED,
        ):
            return None
        return get_image_url(obj.final_key)

    def get_thumbnail_url(self, obj):
        if obj.status not in (
            ImageUpload.Status.READY,
            ImageUpload.Status.ATTACHED,
        ):
            return None
        return get_image_url(obj.thumbnail_key)


class S3ImageRepresentationMixin:
    s3_image_field = 'image'
    s3_upload_field = 'image_upload'

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data[self.s3_image_field] = get_entity_image_url(
            instance,
            image_field=self.s3_image_field,
            upload_field=self.s3_upload_field,
            request=self.context.get('request'),
        )

        return data
