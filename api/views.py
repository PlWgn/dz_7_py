from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, DjangoModelPermissions
from rest_framework.response import Response

from employees.models import Skill, User
from workplaces.models import Workplace

from .filters import EmployeeFilter
from .permissions import CanMoveEmployees
from .serializers import (
    EmployeeDetailSerializer,
    EmployeeSerializer,
    MoveSerializer,
    SkillSerializer,
    WorkplaceSerializer,
)


class EmployeeViewSet(viewsets.ModelViewSet):
    filterset_class = EmployeeFilter

    def get_queryset(self):
        queryset = (
            User.objects.filter(is_superuser=False)
            .select_related('workplace')
            .prefetch_related('employee_skills__skill')
            .order_by('id')
        )
        if self.action != 'list':
            queryset = queryset.prefetch_related('photos')
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeSerializer
        if self.action == 'move':
            return MoveSerializer
        return EmployeeDetailSerializer

    def get_permissions(self):
        # каталог открыт всем, остальное по правам роли
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'move':
            return [CanMoveEmployees()]
        return [DjangoModelPermissions()]

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        employee = self.get_object()
        serializer = MoveSerializer(
            data=request.data, context={'employee': employee}
        )
        serializer.is_valid(raise_exception=True)
        desk_number = serializer.validated_data['desk_number']
        try:
            with transaction.atomic():
                Workplace.objects.filter(employee=employee).exclude(
                    desk_number=desk_number
                ).update(employee=None)
                workplace = Workplace.objects.get(desk_number=desk_number)
                workplace.employee = employee
                workplace.save()
        except ValidationError as err:
            raise serializers.ValidationError({'desk_number': err.messages})
        employee = self.get_queryset().get(pk=employee.pk)
        return Response(
            EmployeeDetailSerializer(
                employee, context={'request': request}
            ).data
        )


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class WorkplaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Workplace.objects.select_related('employee')
    serializer_class = WorkplaceSerializer
