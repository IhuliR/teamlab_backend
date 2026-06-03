import django_filters
from django.contrib.auth import get_user_model

from projects.models import Project


User = get_user_model()


class ProjectFilter(django_filters.FilterSet):
    skill_ids = django_filters.BaseInFilter(
        field_name='roles__skill_requirements__skill_id',
        lookup_expr='in',
    )
    specialization_ids = django_filters.BaseInFilter(
        field_name='roles__specialization_id',
        lookup_expr='in',
    )

    class Meta:
        model = Project
        fields = (
            'field_id',
            'status',
            'skill_ids',
            'specialization_ids',
        )


class UserFilter(django_filters.FilterSet):
    field_id = django_filters.NumberFilter(
        field_name='specialization__field_id',
    )
    specialization_ids = django_filters.BaseInFilter(
        field_name='specialization_id',
        lookup_expr='in',
    )
    skill_ids = django_filters.BaseInFilter(
        field_name='skills__skill_id',
        lookup_expr='in',
    )

    class Meta:
        model = User
        fields = (
            'account_type',
            'field_id',
            'specialization_ids',
            'skill_ids',
            'level',
            'work_format',
            'employment_type',
            'search_status',
            'city',
        )