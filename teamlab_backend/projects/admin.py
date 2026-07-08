from django.contrib import admin

from .models import (
    Project,
    Field,
    Specialization,
    ProjectMembership,
    ProjectRole,
    ProjectRoleSkill,
    RoleInterest
)


class ProjectRoleInline(admin.TabularInline):
    model = ProjectRole
    extra = 0
    autocomplete_fields = ('specialization',)
    fields = (
        'specialization',
        'created_at',
        'updated_at',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    show_change_link = True


class ProjectRoleSkillInline(admin.TabularInline):
    model = ProjectRoleSkill
    extra = 0
    autocomplete_fields = ('skill',)
    fields = (
        'skill',
        'description',
        'order',
    )
    ordering = ('order',)


class RoleInterestInline(admin.TabularInline):
    model = RoleInterest
    extra = 0
    can_delete = False
    show_change_link = True
    fields = (
        'user',
        'source',
        'reviewed_at',
        'created_at',
        'updated_at',
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_featured',
        'featured_order',
    )
    list_editable = (
        'is_featured',
        'featured_order',
    )
    search_fields = ('name',)
    list_filter = ('is_featured',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = (ProjectRoleInline,)
    list_display = (
        'title',
        'owner',
        'field',
        'status',
        'is_featured',
        'featured_order',
        'created_at',
        'updated_at',
    )
    list_editable = (
        'is_featured',
        'featured_order',
    )
    search_fields = (
        'title',
        'owner__username',
        'owner__email',
        'field__name'
    )
    list_filter = (
        'field',
        'status',
        'is_featured',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = (
        'owner',
        'field',
    )


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'field',
    )
    search_fields = ('name',)
    list_filter = ('field',)


@admin.register(ProjectRole)
class ProjectRoleAdmin(admin.ModelAdmin):
    inlines = (
        ProjectRoleSkillInline,
        RoleInterestInline,
    )
    list_display = (
        'project',
        'specialization',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'project__title',
        'specialization__name',
    )
    list_filter = (
        'project__field',
        'project__status',
        'specialization',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = (
        'project',
        'specialization',
    )


@admin.register(ProjectRoleSkill)
class ProjectRoleSkillAdmin(admin.ModelAdmin):
    list_display = (
        'project_role',
        'skill',
        'order'
    )
    search_fields = (
        'project_role__project__title',
        'project_role__specialization__name',
        'skill__name',
    )
    list_filter = (
        'project_role',
        'skill'
    )


@admin.register(RoleInterest)
class RoleInterestAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'project_role',
        'source',
        'status',
        'reviewed_at',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'user__username',
        'user__email',
        'project_role__project__title',
        'project_role__specialization__name',
    )
    list_filter = (
        'source',
        'status',
        'project_role__project__field',
        'project_role__project__status',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = (
        'user',
        'project_role'
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'project_role',
        'role_interest',
        'status',
        'joined_at',
        'ended_at',
    )
    search_fields = (
        'user__username',
        'user__email',
        'project_role__project__title',
        'project_role__specialization__name',
        'role_interest__user__username',
        'role_interest__user__email',
    )
    list_filter = (
        'status',
        'project_role__project__field',
        'project_role__project__status',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = (
        'user',
        'project_role',
        'role_interest',
    )
    readonly_fields = (
        'joined_at',
        'created_at',
        'updated_at',
    )


admin.site.empty_value_display = 'Не задано'
