from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from projects.models import (
    Project,
    ProjectMembership,
    ProjectRole,
    RoleInterest,
    Specialization
)
from users.models import UserSkill, Skill, PortfolioWork, FavoriteProject
from users.services import (
    replace_user_skills,
    user_has_active_participation_or_pending_interests
)
from .projects import FavoriteProjectRolePreviewSerializer

User = get_user_model()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserSkillReadSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    skill_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        source='skill.name',
        read_only=True,
    )

    class Meta:
        model = UserSkill
        fields = (
            'id',
            'user_id',
            'skill_id',
            'name',
            'level',
            'created_at',
            'updated_at'
        )
        read_only_fields = fields


class UserSkillInputSerializer(serializers.Serializer):
    skill_id = serializers.PrimaryKeyRelatedField(
        source='skill',
        queryset=Skill.objects.all(),
    )
    level = serializers.ChoiceField(
        choices=UserSkill.Level.choices,
    )


class UserListSerializer(serializers.ModelSerializer):
    specialization_id = serializers.IntegerField(read_only=True)
    specialization_name = serializers.CharField(
        source='specialization.name',
        read_only=True,
    )
    skills = UserSkillReadSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'avatar',
            'specialization_id',
            'specialization_name',
            'level',
            'city',
            'workload_hours_per_week',
            'work_format',
            'employment_type',
            'skills',
            'search_status'
        )
        read_only_fields = fields


class PortfolioWorkReadSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    
    class Meta:
        model = PortfolioWork
        fields = (
            'id',
            'user_id',
            'title',
            'task',
            'solution',
            'image',
            'technologies',
            'link',
            'created_at',
            'updated_at'
        )
        read_only_fields = fields


class PortfolioWorkWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    technologies = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    link = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = PortfolioWork
        fields = (
            'id',
            'title',
            'task',
            'solution',
            'image',
            'technologies',
            'link',
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = validated_data.pop('user')
        return PortfolioWork.objects.create(
            user=user,
            **validated_data,
        )


class UserDetailSerializer(serializers.ModelSerializer):
    specialization_id = serializers.IntegerField(read_only=True)
    specialization_name = serializers.CharField(
        source='specialization.name',
        read_only=True,
        allow_null=True,
    )
    skills = UserSkillReadSerializer(
        many=True,
        read_only=True,
    )
    portfolio_works = PortfolioWorkReadSerializer(
        many=True,
        read_only=True,
    )
    contacts_visible = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    matching_project_role_id = serializers.SerializerMethodField()
    matching_project_role_name = serializers.SerializerMethodField()
    project_interest_id = serializers.SerializerMethodField()
    project_interest_status = serializers.SerializerMethodField()
    project_interest_source = serializers.SerializerMethodField()
    project_membership_id = serializers.SerializerMethodField()
    project_membership_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'bio',
            'specialization_id',
            'specialization_name',
            'level',
            'workload_hours_per_week',
            'work_format',
            'employment_type',
            'search_status',
            'city',
            'avatar',
            'contacts_visible',
            'social_links',
            'matching_project_role_id',
            'matching_project_role_name',
            'project_interest_id',
            'project_interest_status',
            'project_interest_source',
            'project_membership_id',
            'project_membership_status',
            'created_at',
            'updated_at',
            'skills',
            'portfolio_works',
        )
        read_only_fields = fields

    def _get_request_user(self):
        request = self.context.get('request')

        if request is None or not request.user.is_authenticated:
            return None

        return request.user

    def _get_owner_project(self):
        user = self._get_request_user()

        if user is None:
            return None

        cache = self.context.setdefault('owner_project_cache', {})

        if user.pk not in cache:
            cache[user.pk] = Project.objects.filter(
                owner=user,
            ).order_by('id').first()

        return cache[user.pk]

    def _get_project_interest(self, obj):
        project = self._get_owner_project()

        if project is None:
            return None

        cache = self.context.setdefault('project_interests_cache', {})

        if obj.pk not in cache:
            cache[obj.pk] = RoleInterest.objects.filter(
                user=obj,
                project_role__project=project,
            ).select_related(
                'project_role',
                'project_role__specialization',
            ).order_by('-created_at').first()

        return cache[obj.pk]

    def _get_project_membership(self, obj):
        project = self._get_owner_project()

        if project is None:
            return None

        cache = self.context.setdefault('project_memberships_cache', {})

        if obj.pk not in cache:
            cache[obj.pk] = ProjectMembership.objects.filter(
                user=obj,
                project_role__project=project,
            ).select_related(
                'project_role',
                'project_role__specialization',
            ).order_by('-created_at').first()

        return cache[obj.pk]

    def _get_matching_project_role(self, obj):
        project = self._get_owner_project()

        if project is None:
            return None

        cache = self.context.setdefault('matching_project_roles_cache', {})

        if obj.pk not in cache:
            membership = self._get_project_membership(obj)

            if membership is not None:
                cache[obj.pk] = membership.project_role
                return cache[obj.pk]

            interest = self._get_project_interest(obj)

            if interest is not None:
                cache[obj.pk] = interest.project_role
                return cache[obj.pk]

            if not obj.specialization_id:
                cache[obj.pk] = None
                return None

            cache[obj.pk] = ProjectRole.objects.filter(
                project=project,
                specialization_id=obj.specialization_id,
            ).select_related(
                'specialization',
            ).order_by('id').first()

        return cache[obj.pk]

    def _get_contacts_visible(self, obj):
        user = self._get_request_user()

        if user is None:
            return False

        cache = self.context.setdefault('contacts_visible_cache', {})

        if obj.pk not in cache:
            if user == obj:
                cache[obj.pk] = True
            elif obj.profile_visibility == User.ProfileVisibility.HIDDEN:
                cache[obj.pk] = False
            elif obj.profile_visibility == User.ProfileVisibility.PUBLIC:
                cache[obj.pk] = True
            else:
                cache[obj.pk] = ProjectMembership.objects.filter(
                    user=obj,
                    project_role__project__owner=user,
                    status=ProjectMembership.Status.ACTIVE,
                ).exists()

        return cache[obj.pk]

    def get_matching_project_role_id(self, obj):
        role = self._get_matching_project_role(obj)
        return role.id if role else None

    def get_matching_project_role_name(self, obj):
        role = self._get_matching_project_role(obj)
        return role.specialization.name if role else None

    def get_project_interest_id(self, obj):
        interest = self._get_project_interest(obj)
        return interest.id if interest else None

    def get_project_interest_status(self, obj):
        interest = self._get_project_interest(obj)
        return interest.status if interest else None

    def get_project_interest_source(self, obj):
        interest = self._get_project_interest(obj)
        return interest.source if interest else None

    def get_project_membership_id(self, obj):
        membership = self._get_project_membership(obj)
        return membership.id if membership else None

    def get_project_membership_status(self, obj):
        membership = self._get_project_membership(obj)
        return membership.status if membership else None

    def get_contacts_visible(self, obj):
        return self._get_contacts_visible(obj)

    def get_social_links(self, obj):
        if self._get_contacts_visible(obj):
            return obj.social_links

        return None


class CurrentUserDetailSerializer(serializers.ModelSerializer):
    specialization_id = serializers.IntegerField(read_only=True)
    specialization_name = serializers.CharField(
        source='specialization.name',
        read_only=True,
        allow_null=True,
    )
    skills = UserSkillReadSerializer(
        many=True,
        read_only=True
    )
    portfolio_works = PortfolioWorkReadSerializer(
        many=True,
        read_only=True,
    )
    owned_project_ids = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'bio',
            'account_type',
            'specialization_id',
            'specialization_name',
            'level',
            'workload_hours_per_week',
            'work_format',
            'employment_type',
            'search_status',
            'profile_visibility',
            'notification_enabled',
            'city',
            'social_links',
            'avatar',
            'skills',
            'portfolio_works',
            'owned_project_ids',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
    
    def get_owned_project_ids(self, obj):
        return list(
            obj.owned_projects.order_by('id').values_list('id', flat=True)
        )


class CurrentUserUpdateSerializer(serializers.ModelSerializer):
    specialization_id = serializers.PrimaryKeyRelatedField(
        source='specialization',
        queryset=Specialization.objects.all(),
        required=False,
        allow_null=True,
    )
    skills = UserSkillInputSerializer(
        many=True,
        required=False,
        allow_empty=False,
    )
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'username',
            'bio',
            'specialization_id',
            'level',
            'workload_hours_per_week',
            'work_format',
            'employment_type',
            'search_status',
            'profile_visibility',
            'notification_enabled',
            'city',
            'social_links',
            'avatar',
            'skills',
        )

    def validate(self, attrs):
        new_specialization = attrs.get(
            'specialization',
            self.instance.specialization,
        )

        if (
            self.instance.account_type == User.AccountType.PARTICIPANT
            and new_specialization is None
        ):
            raise serializers.ValidationError({
                'specialization_id': (
                    'Для участника специализация обязательна.'
                )
            })
        if (
            'specialization' in attrs
            and attrs['specialization'] != self.instance.specialization
            and user_has_active_participation_or_pending_interests(
                self.instance
            )
        ):
            raise serializers.ValidationError({
                'specialization_id': (
                    'Нельзя изменить специализацию при активном участии, '
                    'заявках или приглашениях.'
                )
            })

        return attrs

    def update(self, instance, validated_data):
        skills_data = validated_data.pop('skills', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if skills_data is not None:
            replace_user_skills(instance, skills_data)

        return instance


class FavoriteProjectCardSerializer(serializers.ModelSerializer):
    roles_preview = FavoriteProjectRolePreviewSerializer(
        source='roles',
        many=True,
        read_only=True
    )

    class Meta:
        model = Project
        fields = (
            'id',
            'title',
            'image',
            'roles_preview'
        )
        read_only_fields = fields


class FavoriteProjectCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        source='project',
        queryset=Project.objects.all()
    )

    class Meta:
        model = FavoriteProject
        fields = (
            'id',
            'user_id',
            'project_id',
            'created_at',
        )
        read_only_fields = (
            'id',
            'user_id',
            'created_at'
        )

    def validate(self, attrs):
        request = self.context['request']

        if FavoriteProject.objects.filter(
            user=request.user,
            project=attrs['project'],
        ).exists():
            raise serializers.ValidationError(
                'Проект уже добавлен в избранное.'
            )
        
        return attrs

    def create(self, validated_data):
        user = validated_data.pop('user')
        return FavoriteProject.objects.create(
            user=user,
            **validated_data,
        )


class FavoriteProjectReadSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    project_id = serializers.IntegerField(read_only=True)
    project = FavoriteProjectCardSerializer(read_only=True)

    class Meta:
        model = FavoriteProject
        fields = (
            'id',
            'user_id',
            'project_id',
            'project',
            'created_at',
        )
        read_only_fields = fields
