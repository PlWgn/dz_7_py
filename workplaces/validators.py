from django.apps import apps
from django.core.exceptions import ValidationError


def get_roles(employee) -> set:
    categories = set(employee.skills.values_list('category', flat=True))
    return categories & {'developer', 'tester'}


def validate_neighbors(workplace):
    # тестировщики и разработчики не могут сидеть за соседними столами
    if workplace.employee is None:
        return
    roles = get_roles(workplace.employee)
    if not roles:
        return
    workplace_model = apps.get_model('workplaces', 'Workplace')
    neighbors = (
        workplace_model.objects.filter(
            desk_number__in=[
                workplace.desk_number - 1,
                workplace.desk_number + 1,
            ],
            employee__isnull=False,
        )
        .exclude(employee=workplace.employee)
        .select_related('employee')
    )
    for neighbor in neighbors:
        neighbor_roles = get_roles(neighbor.employee)
        is_conflict = (
            'tester' in roles and 'developer' in neighbor_roles
        ) or ('developer' in roles and 'tester' in neighbor_roles)
        if is_conflict:
            raise ValidationError(
                f'Нельзя посадить сотрудника за стол '
                f'№{workplace.desk_number}: за соседним столом '
                f'№{neighbor.desk_number} сидит {neighbor.employee}. '
                'Тестировщики и разработчики не могут сидеть '
                'за соседними столами.'
            )
