from django.db import transaction
from rest_framework import serializers

from employees.models import EmployeePhoto, EmployeeSkill, Skill, User
from workplaces.models import Workplace


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name', 'category')


class EmployeeSkillSerializer(serializers.ModelSerializer):
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all())
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = EmployeeSkill
        fields = ('skill', 'skill_name', 'level')


class EmployeePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeePhoto
        fields = ('id', 'image', 'order')


class EmployeeSerializer(serializers.ModelSerializer):
    skills = EmployeeSkillSerializer(
        source='employee_skills', many=True, required=False
    )
    desk_number = serializers.SerializerMethodField()
    experience_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'patronymic',
            'gender',
            'description',
            'hire_date',
            'experience_days',
            'desk_number',
            'skills',
        )

    def get_desk_number(self, employee: User) -> int | None:
        workplace = getattr(employee, 'workplace', None)
        return workplace.desk_number if workplace else None

    def validate_skills(self, skills: list):
        skill_ids = [item['skill'].id for item in skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise serializers.ValidationError('Навыки не должны повторяться')
        return skills

    def save_skills(self, employee: User, skills: list):
        EmployeeSkill.objects.bulk_create(
            EmployeeSkill(
                employee=employee, skill=item['skill'], level=item['level']
            )
            for item in skills
        )

    @transaction.atomic
    def create(self, validated_data: dict):
        skills = validated_data.pop('employee_skills', [])
        employee = User(**validated_data)
        # сотрудник из API не входит в систему, пока ему не зададут пароль
        employee.set_unusable_password()
        employee.save()
        self.save_skills(employee, skills)
        return employee

    @transaction.atomic
    def update(self, employee: User, validated_data: dict):
        skills = validated_data.pop('employee_skills', None)
        employee = super().update(employee, validated_data)
        if skills is not None:
            employee.employee_skills.all().delete()
            self.save_skills(employee, skills)
        return employee


class EmployeeDetailSerializer(EmployeeSerializer):
    photos = EmployeePhotoSerializer(many=True, read_only=True)

    class Meta(EmployeeSerializer.Meta):
        fields = EmployeeSerializer.Meta.fields + ('photos',)


class MoveSerializer(serializers.Serializer):
    desk_number = serializers.IntegerField(min_value=1)

    def validate_desk_number(self, desk_number: int):
        workplace = Workplace.objects.filter(desk_number=desk_number).first()
        if workplace is None:
            raise serializers.ValidationError(f'Стола №{desk_number} нет')
        if (
            workplace.employee_id is not None
            and workplace.employee_id != self.context['employee'].id
        ):
            raise serializers.ValidationError(f'Стол №{desk_number} уже занят')
        return desk_number


class WorkplaceSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField()

    class Meta:
        model = Workplace
        fields = ('id', 'desk_number', 'description', 'employee')
