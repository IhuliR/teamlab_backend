from django.contrib.auth import get_user_model
from rest_framework import serializers

from .users import UserListSerializer
from projects.models import ProjectMembership, RoleInterest


User = get_user_model()

class CurrentUserMembershipProjectCardSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(
        source='project_role.project_id',
        read_only=True,
    )
    project_title = serializers.CharField(
        source='project_role.project.title',
        read_only=True,
    )
    project_image = serializers.ImageField(
        source='project_role.project.image',
        read_only=True,
    )
    project_role_id = serializers.IntegerField(read_only=True)
    project_role_name = serializers.CharField(
        source='project_role.specialization.name',
        read_only=True,
    )

    class Meta:
        model = ProjectMembership
        fields = (
            'id',
            'project_id',
            'project_title',
            'project_image',
            'project_role_id',
            'project_role_name',
            'status'
        )
        read_only_fields = fields


class CurrentUserInvitedProjectCardSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(
        source='project_role.project_id',
        read_only=True,
    )
    project_title = serializers.CharField(
        source='project_role.project.title',
        read_only=True,
    )
    project_image = serializers.ImageField(
        source='project_role.project.image',
        read_only=True,
    )
    project_role_id = serializers.IntegerField(read_only=True)
    project_role_name = serializers.CharField(
        source='project_role.specialization.name',
        read_only=True,
    )

    class Meta:
        model = RoleInterest
        fields = (
            'id',
            'project_id',
            'project_title',
            'project_image',
            'project_role_id',
            'project_role_name',
            'source',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class CurrentUserApplicationCardSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    project_role_id = serializers.IntegerField(read_only=True)
    project_id = serializers.IntegerField(
        source='project_role.project_id',
        read_only=True,
    )
    project_title = serializers.CharField(
        source='project_role.project.title',
        read_only=True,
    )
    project_role_name = serializers.CharField(
        source='project_role.specialization.name',
        read_only=True,
    )


    class Meta:
        model = RoleInterest
        fields = (
            'id',
            'user_id',
            'project_id',
            'project_title',
            'project_role_id',
            'project_role_name',
            'source',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class CurrentUserNotificationSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(
        source='project_role.project_id',
        read_only=True,
    )
    project_title = serializers.CharField(
        source='project_role.project.title',
        read_only=True,
    )
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(
        source='user.username',
        read_only=True,
    )
    project_role_id = serializers.IntegerField(read_only=True)
    project_role_name = serializers.CharField(
        source='project_role.specialization.name',
        read_only=True,
    )

    class Meta:
        model = RoleInterest
        fields = (
            'id',
            'source',
            'status',
            'user_id',
            'username',
            'project_id',
            'project_title',
            'project_role_id',
            'project_role_name',
            'created_at',
        )
        read_only_fields = fields


class ProjectInvitationCardSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(
        source='user.username',
        read_only=True,
    )
    project_role_id = serializers.IntegerField(read_only=True)
    project_role_name = serializers.CharField(
        source='project_role.specialization.name',
        read_only=True,
    )

    class Meta:
        model = RoleInterest
        fields = (
            'id',
            'user_id',
            'username',
            'project_role_id',
            'project_role_name',
            'source',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class ProjectApplicationCardSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    project_role_id = serializers.IntegerField(read_only=True)
    project_role_name = serializers.CharField(
        source='project_role.specialization.name',
        read_only=True,
    )
    
    class Meta:
        model = RoleInterest
        fields = (
            'id',
            'user',
            'project_role_id',
            'project_role_name',
            'source',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class ProjectInvitationCreateSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.all(),
    )


class RoleInterestActionResultSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(
        source='user.username',
        read_only=True,
    )
    project_id = serializers.IntegerField(
        source='project_role.project_id',
        read_only=True,
    )
    project_title = serializers.CharField(
        source='project_role.project.title',
        read_only=True,
    )
    project_role_id = serializers.IntegerField(read_only=True)
    project_role_name = serializers.CharField(
        source='project_role.specialization.name',
        read_only=True,
    )
    membership_id = serializers.SerializerMethodField()
    membership_status = serializers.SerializerMethodField()

    class Meta:
        model = RoleInterest
        fields = (
            'id',
            'user_id',
            'username',
            'project_id',
            'project_title',
            'project_role_id',
            'project_role_name',
            'source',
            'status',
            'membership_id',
            'membership_status',
            'reviewed_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def _get_membership(self, obj):
        cache = self.context.setdefault('role_interest_memberships_cache', {})

        if obj.pk not in cache:
            cache[obj.pk] = ProjectMembership.objects.filter(
                role_interest=obj,
            ).first()

        return cache[obj.pk]

    def get_membership_id(self, obj):
        membership = self._get_membership(obj)
        return membership.id if membership else None

    def get_membership_status(self, obj):
        membership = self._get_membership(obj)
        return membership.status if membership else None


class ProjectMembershipActionResultSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(
        source='user.username',
        read_only=True,
    )
    project_role_id = serializers.IntegerField(read_only=True)
    project_role_name = serializers.CharField(
        source='project_role.specialization.name',
        read_only=True,
    )
    project_id = serializers.IntegerField(
        source='project_role.project_id',
        read_only=True,
    )
    project_title = serializers.CharField(
        source='project_role.project.title',
        read_only=True,
    )

    class Meta:
        model = ProjectMembership
        fields = (
            'id',
            'user_id',
            'username',
            'project_id',
            'project_title',
            'project_role_id',
            'project_role_name',
            'status',
            'joined_at',
            'ended_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
