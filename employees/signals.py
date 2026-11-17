from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import EmployeePhoto


@receiver(post_delete, sender=EmployeePhoto)
def delete_photo_file(sender, instance: EmployeePhoto, **kwargs):
    # файл удаляем с диска вместе с записью
    instance.image.delete(save=False)
