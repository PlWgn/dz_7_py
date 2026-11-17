from django.conf import settings
from django.db import models

from .validators import validate_neighbors


class Workplace(models.Model):
    desk_number = models.PositiveIntegerField('Номер стола', unique=True)
    description = models.TextField('Дополнительная информация', blank=True)
    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workplace',
        verbose_name='Сотрудник',
    )

    class Meta:
        verbose_name = 'Рабочее место'
        verbose_name_plural = 'Рабочие места'
        ordering = ['desk_number']

    def __str__(self):
        return f'Стол №{self.desk_number}'

    def clean(self):
        validate_neighbors(self)

    def save(self, *args, **kwargs):
        # проверка обязательна при любом сохранении, а не только в админке
        self.full_clean()
        super().save(*args, **kwargs)
