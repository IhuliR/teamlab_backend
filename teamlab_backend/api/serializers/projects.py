from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
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
from projects.services import (
    create_project_role_skills,
    create_project_with_roles,
    replace_project_role_skills
)
from users.models import (
    FavoriteProject,
    Skill
)


class ProjectRoleSkillReadSerializer(serializers.ModelSerializer):
    skill_id = serializers.IntegerField(read_only=True)
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
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


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
    pass


class ProjectRoleCreateSerializer(ProjectRoleBaseInputSerializer):
    project_id = serializers.PrimaryKeyRelatedField(
        source='project',
        queryset=Project.objects.all(),
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        project = attrs.get('project')
        specialization = attrs.get('specialization')

        if ProjectRole.objects.filter(
            project=project,
            specialization=specialization,
        ).exists():
            raise serializers.ValidationError({
                'specialization_id': (
                    'В проекте уже есть роль с этой специализацией.'
                )
            })

        return attrs

    def create(self, validated_data):
        skills_data = validated_data.pop('skills')

        with transaction.atomic():
            role = ProjectRole.objects.create(**validated_data)
            create_project_role_skills(role, skills_data)
        
        return role


class ProjectRoleUpdateSerializer(ProjectRoleBaseInputSerializer):

    def validate(self, attrs):
        attrs = super().validate(attrs)

        project = self.instance.project
        specialization = attrs.get(
            'specialization',
            self.instance.specialization,
        )

        if ProjectRole.objects.filter(
            project=project,
            specialization=specialization,
        ).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError({
                'specialization_id': (
                    'В проекте уже есть роль с этой специализацией.'
                )
            })

        return attrs

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
    matching_role_id = serializers.SerializerMethodField()
    matching_role_name = serializers.SerializerMethodField()
    my_interest_id = serializers.SerializerMethodField()
    my_interest_status = serializers.SerializerMethodField()
    my_interest_source = serializers.SerializerMethodField()
    my_membership_id = serializers.SerializerMethodField()
    my_membership_status = serializers.SerializerMethodField()

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
            'matching_role_id',
            'matching_role_name',
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

        cache = self.context.setdefault('project_interests_cache', {})

        if obj.pk not in cache:
            cache[obj.pk] = RoleInterest.objects.filter(
                user=user,
                project_role__project=obj,
            ).select_related(
                'project_role',
                'project_role__specialization',
            ).order_by('-created_at').first()

        return cache[obj.pk]

    def _get_my_membership(self, obj):
        user = self._get_request_user()

        if user is None:
            return None

        cache = self.context.setdefault('project_memberships_cache', {})

        if obj.pk not in cache:
            cache[obj.pk] = ProjectMembership.objects.filter(
                user=user,
                project_role__project=obj,
            ).select_related(
                'project_role',
                'project_role__specialization',
            ).order_by('-created_at').first()

        return cache[obj.pk]

    def _get_matching_role(self, obj):
        user = self._get_request_user()

        if user is None:
            return None

        cache = self.context.setdefault('matching_roles_cache', {})

        if obj.pk not in cache:
            membership = self._get_my_membership(obj)

            if membership is not None:
                cache[obj.pk] = membership.project_role
                return cache[obj.pk]

            interest = self._get_my_interest(obj)

            if interest is not None:
                cache[obj.pk] = interest.project_role
                return cache[obj.pk]

            if not user.specialization_id:
                cache[obj.pk] = None
                return None

            cache[obj.pk] = ProjectRole.objects.filter(
                project=obj,
                specialization_id=user.specialization_id,
            ).select_related(
                'specialization',
            ).order_by('id').first()

        return cache[obj.pk]

    def get_matching_role_id(self, obj):
        role = self._get_matching_role(obj)
        return role.id if role else None

    def get_matching_role_name(self, obj):
        role = self._get_matching_role(obj)
        return role.specialization.name if role else None

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


class ProjectCreateSerializer(serializers.Serializer):
    field_id = serializers.PrimaryKeyRelatedField(
        source='field',
        queryset=Field.objects.all(),
    )
    title = serializers.CharField()
    description = serializers.CharField()
    problem = serializers.CharField()
    image = Base64ImageField()
    roles = ProjectRoleNestedInputSerializer(
        many=True,
        allow_empty=False,
    )

    def validate_roles(self, roles):
        specialization_ids = [
            role['specialization'].id
            for role in roles
        ]

        if len(specialization_ids) != len(set(specialization_ids)):
            raise serializers.ValidationError(
                'В проекте не может быть несколько ролей '
                'с одной специализацией.'
            )

        return roles

    def create(self, validated_data):
        owner = validated_data.pop('owner')
        roles_data = validated_data.pop('roles', [])

        return create_project_with_roles(
            owner=owner,
            roles_data=roles_data,
            project_data=validated_data,
        )


class ProjectUpdateSerializer(serializers.ModelSerializer):
    field_id = serializers.PrimaryKeyRelatedField(
        source='field',
        queryset=Field.objects.all(),
    )
    image = Base64ImageField()

    class Meta:
        model = Project
        fields = (
            'field_id',
            'title',
            'description',
            'problem',
            'image',
            'status',
        )


class FavoriteProjectRolePreviewSerializer(serializers.ModelSerializer):
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
        )
        read_only_fields = fields
