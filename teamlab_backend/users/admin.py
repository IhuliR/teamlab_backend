from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import PortfolioWork, Skill, UserSkill, FavoriteProject

User = get_user_model()


class UserSkillInline(admin.TabularInline):
    model = UserSkill
    extra = 0
    autocomplete_fields = ('skill',)
    fields = ('skill', 'level')


class PortfolioWorkInline(admin.StackedInline):
    model = PortfolioWork
    extra = 0
    show_change_link = True

    fields = (
        'title',
        'task',
        'solution',
        'image',
        'technologies',
        'link',
    )


class FavoriteProjectInline(admin.TabularInline):
    model = FavoriteProject
    extra = 0
    autocomplete_fields = ('project',)
    fields = ('project', 'created_at')
    readonly_fields = ('created_at',)

    def has_add_permission(self, request, obj):
        if obj is None:
            return False
        return obj.account_type == User.AccountType.PARTICIPANT

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return False
        return obj.account_type == User.AccountType.PARTICIPANT

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return False
        return obj.account_type == User.AccountType.PARTICIPANT


@admin.register(User)
class TeamlabUserAdmin(UserAdmin):
    inlines = (
        UserSkillInline,
        PortfolioWorkInline,
        FavoriteProjectInline,
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            'Данные TeamLab',
            {
                'fields': (
                    'display_name',
                    'account_type',
                    'specialization',
                    'level',
                    'workload_hours_per_week',
                    'work_format',
                    'employment_type',
                    'search_status',
                    'profile_visibility',
                    'notification_enabled',
                    'city',
                    'avatar',
                    'bio',
                    'social_links',
                ),
            },
        ),
    )
    autocomplete_fields = ('specialization',)

    list_display = (
        'username',
        'display_name',
        'account_type',
        'specialization',
        'email',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'username',
        'email',
        'display_name',
        'specialization__name',
    )
    list_filter = UserAdmin.list_filter + (
        'account_type',
        'specialization',
        'created_at',
        'updated_at',
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'name',
        'slug',
    )
    list_filter = (
        'created_at',
        'updated_at',
    )
    prepopulated_fields = {
        'slug': ('name',),
    }
    filter_horizontal = (
        'fields',
    )


@admin.register(PortfolioWork)
class PortfolioWorkAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'link',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'created_at',
        'updated_at',
    )
    search_fields = (
        'title',
        'user__username',
        'user__email',
        'task',
        'solution',
    )
    autocomplete_fields = ('user',)
    ordering = ('-created_at',)


admin.site.unregister(Group)
admin.site.empty_value_display = 'Не задано'
