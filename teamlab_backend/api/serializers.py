from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from projects.models import (
    Project,
    ProjectRoleSkill,
    ProjectRole,
    Field,
    Specialization,
)
from users.models import(
    Skill
)

User = get_user_model()


class AuthUserSerializer(serializers.ModelSerializer):
    """Краткие данные пользователя для auth-ответов."""

    class Meta:
        model = User
        fields = ('id', 'username', 'account_type')
        read_only_fields = fields


class TokenLoginSerializer(TokenObtainPairSerializer):
    """JWT-login по username/password с информацией о user в ответе."""

    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = AuthUserSerializer(self.user).data
        return data


class TokenRefreshWithUserSerializer(TokenRefreshSerializer):
    """Refresh access-токена с информацией о user в ответе."""

    def validate(self, attrs):
        data = super().validate(attrs)

        try:
            refresh = RefreshToken(attrs['refresh'])
        except TokenError as error:
            raise InvalidToken(error.args[0])
        
        user_id = refresh[api_settings.USER_ID_CLAIM]
        user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        data['user'] = AuthUserSerializer(user).data
        return data


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

    class Meta:
        model = Skill
        fields = ('id', 'name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class ProjectRoleSkillReadSerializer(serializers.ModelSerializer):
    skill_id = serializers.IntegerField(
        source='skill.id',
        read_only=True
    )
    name = serializers.CharField(
        source='skill.name',
        read_only=True,
    )

    class Meta:
        model = ProjectRoleSkill
        fields = ('id', 'skill_id', 'name', 'description', 'order')
        read_only_fields = fields


class ProjectRoleSkillInputSerializer(serializers.Serializer):
    skill_id = serializers.PrimaryKeyRelatedField(
        source='skill',
        queryset=Skill.objects.all(),
    )
    description = serializers.CharField()
    order = serializers.IntegerField()


class ProjectRoleReadSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(read_only=True)
    specialization_id = serializers.IntegerField(read_only=True)
    skills = ProjectRoleSkillReadSerializer(
        source='skill_requirements',
        many=True,
        read_only=True
    )
    my_interest_id = serializers.SerializerMethodField()
    my_interest_status = serializers.SerializerMethodField()
    my_interest_source = serializers.SerializerMethodField()
    my_membership_id = serializers.SerializerMethodField()
    my_membership_status = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectRole
        fields = (
            'id',
            'project_id',
            'specialization_id',
            'tasks',
            'benefits',
            'skills',
            'is_open',
            'my_interest_id',
            'my_interest_status',
            'my_interest_source',
            'my_membership_id',
            'my_membership_status',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
    
    def get_my_interest_id(self, obj):
        ...
    
    def get_my_interest_status(self, obj):
        ...
    
    def get_my_interest_source(self, obj):
        ...
    
    def get_my_membership_id(self, obj):
        ...
    
    def get_my_membership_status(self, obj):
        ...


class ProjectRolePreviewSerializer(serializers.ModelSerializer):
    skills = ProjectRoleSkillReadSerializer(
        source='skill_requirements',
        many=True,
        read_only=True
    )
    specialization_id = serializers.IntegerField(read_only=True)
    specialization_name = serializers.CharField(
        source='specialization.name',
        read_only=True
    )

    class Meta:
        model = ProjectRole
        fields = (
            'id',
            'specialization_id',
            'specialization_name',
            'skills',
            'is_open'
        )
        read_only_fields = fields


class ProjectRoleNestedInputSerializer(serializers.Serializer):
    serialization_id = serializers.PrimaryKeyRelatedField(
        source='specialization',
        queryset=Specialization.objects.all()
    )
    tasks = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    benifits = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    skills = ProjectRoleSkillInputSerializer(
        many=True,
        allow_empty=False
    )


class ProjectRoleCreateSerializer(serializers.Serializer):
    project_id = serializers.PrimaryKeyRelatedField(
        source='project',
        queryset=Project.objects.all(),
    )
    serialization_id = serializers.PrimaryKeyRelatedField(
        source='specialization',
        queryset=Specialization.objects.all()
    )
    tasks = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    benifits = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    skills = ProjectRoleSkillInputSerializer(
        many=True,
        allow_empty=False
    )


class ProjectRoleUpdateSerializer(serializers.ModelSerializer):
    specialization_id = serializers.PrimaryKeyRelatedField(
        source='specialization',
        queryset=Specialization.objects.all()
    )
    task = serializers.ListField(
        child
    )
    
    class Meta:
        model = ProjectRole
        fields = (
            'specialization_id',
            'tasks',
            'benefits',
            'skills',
            'is_open'
        )


class ProjectListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = (
            'id',
            'owner_id',
            'field_id',
            'title',
            'description',
            'problem',
            'image',
            'status',
            'is_favorited',
            'roles_preview',
            'created_at',
            'updated_at'
        )
