from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import Skill

User = get_user_model()


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
    )
    search_fields = (
        'username',
        'email',
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
    prepopulated_fields = {
        'slug': ('name',),
    }
    filter_horizontal = (
        'fields',
    )


admin.site.unregister(Group)
