import django_filters

from projects.models import Project


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