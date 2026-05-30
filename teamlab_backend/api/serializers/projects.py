import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from projects.models import (
    Project,
    ProjectMembership,
    ProjectRoleSkill,
    ProjectRole,
    RoleInterest,
    Field,
    Specialization,
)
from projects.services import(
    create_project_role_skills,
    replace_project_role_skills
)
from users.models import(
    FavoriteProject,
    Skill
)


User = get_user_model()


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
    specialization_name = serializers.CharField(
        source='specialization.name',
        read_only=True,
    )
    
    class Meta:
        model = ProjectRole
        fields = (
            'id',
            'project_id',
            'specialization_id',
            'specialization_name',
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

    def _get_request_user(self):
        request = self.context.get('request')

        if request is None or not request.user.is_authenticated:
            return None
        
        return request.user
    
    def _get_my_interest(self, obj):
        user = self._get_request_user()

        if user is None:
            return None
        
        cache = self.context.setdefault('my_interests_cache', {})

        if obj.pk not in cache:
            cache[obj.pk] = RoleInterest.objects.filter(
                user=user,
                project_role=obj,
            ).first()
        
        return cache[obj.pk]
    
    def _get_my_membership(self, obj):
        user = self._get_request_user()

        if user is None:
            return None
        
        cache = self.context.get('my_membership_cache', {})

        if obj.pk not in cache:
            cache[obj.pk] = ProjectMembership.objects.filter(
                user=user,
                project_role=obj,
            ).order_by('-created_at').first()

        return cache[obj.pk]

    def get_my_interest_id(self, obj):
        interest = self._get_my_interest(obj)
        return interest.id if interest else None
    
    def get_my_interest_status(self, obj):
        interest = self._get_my_interest(obj)
        return interest.status if interest else None
    
    def get_my_interest_source(self, obj):
        interest = self._get_my_interest(obj)
        return interest.source if interest else None
    
    def get_my_membership_id(self, obj):
        membership = self._get_my_membership(obj)
        return membership.id if membership else None
    
    def get_my_membership_status(self, obj):
        membership = self._get_my_membership(obj)
        return membership.status if membership else None


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


class ProjectRoleBaseInputSerializer(serializers.Serializer):
    specialization_id = serializers.PrimaryKeyRelatedField(
        source='specialization',
        queryset=Specialization.objects.all()
    )
    tasks = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    benefits = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    skills = ProjectRoleSkillInputSerializer(
        many=True,
        allow_empty=False
    )


class ProjectRoleNestedInputSerializer(ProjectRoleBaseInputSerializer):
    ...


class ProjectRoleCreateSerializer(ProjectRoleBaseInputSerializer):
    project_id = serializers.PrimaryKeyRelatedField(
        source='project',
        queryset=Project.objects.all(),
    )

    def create(self, validated_data):
        skills_data = validated_data.pop('skills')

        with transaction.atomic():
            role = ProjectRole.objects.create(**validated_data)
            create_project_role_skills(role, skills_data)
        
        return role


class ProjectRoleUpdateSerializer(ProjectRoleBaseInputSerializer):
    is_open = serializers.BooleanField()

    def update(self, instance, validated_data):
        skills_data = validated_data.pop('skills', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            instance.save()

            if skills_data is not None:
                replace_project_role_skills(instance, skills_data)
        
        return instance
    

class ProjectBaseReadSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(read_only=True)
    field_id = serializers.IntegerField(read_only=True)
    is_favorited = serializers.SerializerMethodField()

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
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')

        if request is None or not request.user.is_authenticated:
            return False
        
        return FavoriteProject.objects.filter(
            user=request.user,
            project=obj,
        ).exists()


class ProjectListSerializer(ProjectBaseReadSerializer):
    roles_preview = ProjectRolePreviewSerializer(
        source='roles',
        many=True,
        read_only=True
    )

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
            'updated_at',
        )
        read_only_fields = fields


class ProjectDetailSerializer(ProjectBaseReadSerializer):
    roles = ProjectRoleReadSerializer(
        many=True,
        read_only=True
    )

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
            'roles',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):

        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class ProjectCreateSerializer(serializers.Serializer):
    field_id = serializers.PrimaryKeyRelatedField(
        source='field',
        queryset=Field.objects.all(),
    )
    title = serializers.CharField()
    description = serializers.CharField()
    problem = serializers.CharField()
    image = Base64ImageField()

    def create(self, validated_data):
        return super().create(validated_data)
