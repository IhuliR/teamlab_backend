import django_filters
from django.contrib.auth import get_user_model

from projects.models import Project
from users.models import Skill


User = get_user_model()


class NumberInFilret(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class ProjectFilter(django_filters.FilterSet):
    field_ids = NumberInFilret(
        field_name='field_id',
        lookup_expr='in',
    )
    skill_ids = NumberInFilret(
        field_name='roles__skill_requirements__skill_id',
        lookup_expr='in',
        distinct=True,
    )
    specialization_ids = django_filters.BaseInFilter(
        field_name='roles__specialization_id',
        lookup_expr='in',
        distinct=True,
    )

    class Meta:
        model = Project
        fields = (
            'field_id',
            'field_ids',
            'status',
            'skill_ids',
            'specialization_ids',
        )


class UserFilter(django_filters.FilterSet):
    field_id = django_filters.NumberFilter(
        field_name='specialization__field_id',
    )
    field_ids = NumberInFilret(
        field_name='specialization__field__id',
        lookup_expr='in',
    )
    specialization_ids = NumberInFilret(
        field_name='specialization_id',
        lookup_expr='in',
    )
    skill_ids = NumberInFilret(
        field_name='skills__skill_id',
        lookup_expr='in',
    )

    class Meta:
        model = User
        fields = (
            'account_type',
            'field_id',
            'field_ids',
            'specialization_ids',
            'skill_ids',
            'level',
            'work_format',
            'employment_type',
            'search_status',
            'city',
        )

class SkillFilter(django_filters.FilterSet):
    field_ids = NumberInFilret(
        field_name='fields__id',
        lookup_expr='in',
        distinct=True,
    )

    class Meta:
        model = Skill
        fields = (
            'field_ids',
        )
