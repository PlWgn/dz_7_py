from rest_framework.permissions import BasePermission


class CanMoveEmployees(BasePermission):
    message = 'Перемещать сотрудников могут только смотрители и администраторы'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm(
            'workplaces.change_workplace'
        )
