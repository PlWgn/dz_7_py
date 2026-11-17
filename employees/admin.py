from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmployeePhoto, EmployeeSkill, Skill, User


class EmployeeSkillInline(admin.TabularInline):
    model = EmployeeSkill
    extra = 1


class EmployeePhotoInline(admin.TabularInline):
    model = EmployeePhoto
    extra = 1


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    list_editable = ('category',)
    search_fields = ('name',)


@admin.register(User)
class EmployeeAdmin(UserAdmin):
    list_display = (
        'username',
        'last_name',
        'first_name',
        'patronymic',
        'gender',
        'hire_date',
        'is_staff',
    )
    list_filter = ('gender', 'skills', 'is_staff')
    search_fields = ('username', 'last_name', 'first_name', 'patronymic')
    inlines = [EmployeeSkillInline, EmployeePhotoInline]
    fieldsets = UserAdmin.fieldsets + (
        (
            'Данные сотрудника',
            {'fields': ('patronymic', 'gender', 'hire_date', 'description')},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Данные сотрудника',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'patronymic',
                    'gender',
                    'hire_date',
                )
            },
        ),
    )
