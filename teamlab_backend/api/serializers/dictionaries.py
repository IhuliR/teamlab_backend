from rest_framework import serializers

from projects.models import Field, Specialization
from users.models import Skill


class FieldSerializer(serializers.ModelSerializer):

    class Meta:
        model = Field
        fields = ('id', 'name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class SpecializationSerializer(serializers.ModelSerializer):
    field_id = serializers.PrimaryKeyRelatedField(
        source='field',
        queryset=Field.objects.all(),
    )

    class Meta:
        model = Specialization
        fields = ('id', 'field_id', 'name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class SkillSerializer(serializers.ModelSerializer):
    field_ids = serializers.PrimaryKeyRelatedField(
        source='fields',
        many=True,
        read_only=True,
    )

    class Meta:
        model = Skill
        fields = ('id', 'name', 'slug', 'field_ids', 'created_at', 'updated_at')
        read_only_fields = fields
