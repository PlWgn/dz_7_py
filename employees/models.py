from datetime import date

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Skill(models.Model):
    class Category(models.TextChoices):
        DEVELOPER = 'developer', 'Разработка'
        TESTER = 'tester', 'Тестирование'
        OTHER = 'other', 'Другое'

    name = models.CharField('Название', max_length=100, unique=True)
    category = models.CharField(
        'Направление',
        max_length=10,
        choices=Category.choices,
        default=Category.OTHER,
    )

    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = 'male', 'Мужской'
        FEMALE = 'female', 'Женский'

    patronymic = models.CharField('Отчество', max_length=150, blank=True)
    gender = models.CharField(
        'Пол', max_length=6, choices=Gender.choices, blank=True
    )
    description = models.TextField('Описание', blank=True)
    hire_date = models.DateField('Дата приёма на работу', default=date.today)
    skills = models.ManyToManyField(
        Skill,
        through='EmployeeSkill',
        related_name='employees',
        verbose_name='Навыки',
        blank=True,
    )

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        full_name = ' '.join(
            part
            for part in [self.last_name, self.first_name, self.patronymic]
            if part
        )
        return full_name or self.username

    @property
    def experience_days(self):
        return (date.today() - self.hire_date).days


class EmployeeSkill(models.Model):
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='employee_skills',
        verbose_name='Сотрудник',
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='employee_skills',
        verbose_name='Навык',
    )
    level = models.PositiveSmallIntegerField(
        'Уровень освоения',
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='От 1 до 10',
    )

    class Meta:
        verbose_name = 'Навык сотрудника'
        verbose_name_plural = 'Навыки сотрудника'
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'skill'], name='unique_employee_skill'
            ),
        ]

    def __str__(self):
        return f'{self.skill} ({self.level})'


class EmployeePhoto(models.Model):
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Сотрудник',
    )
    image = models.ImageField('Изображение', upload_to='employees/')
    order = models.PositiveIntegerField('Порядковый номер', default=0)

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Галерея'
        ordering = ['order', 'id']

    def __str__(self):
        return f'Фото {self.order} ({self.employee})'
