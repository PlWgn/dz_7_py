from datetime import date, timedelta

from django_filters import rest_framework as filters

from employees.models import Skill, User


class EmployeeFilter(filters.FilterSet):
    skills = filters.ModelMultipleChoiceFilter(
        field_name='skills',
        queryset=Skill.objects.all(),
        conjoined=True,
        label='Навыки (id, все сразу)',
    )
    skill = filters.CharFilter(
        field_name='skills__name', label='Название навыка', distinct=True
    )
    min_experience = filters.NumberFilter(
        method='filter_min_experience', label='Стаж от, дней'
    )
    max_experience = filters.NumberFilter(
        method='filter_max_experience', label='Стаж до, дней'
    )

    class Meta:
        model = User
        fields = (
            'skills',
            'skill',
            'gender',
            'min_experience',
            'max_experience',
        )

    def filter_min_experience(self, queryset, name: str, value):
        return queryset.filter(
            hire_date__lte=date.today() - timedelta(days=int(value))
        )

    def filter_max_experience(self, queryset, name: str, value):
        return queryset.filter(
            hire_date__gte=date.today() - timedelta(days=int(value))
        )
