from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

KEEPER_PERMISSIONS = [
    'view_user',
    'view_skill',
    'view_employeeskill',
    'view_employeephoto',
    'view_workplace',
    'change_workplace',
]

ADMIN_MODELS = ['user', 'skill', 'employeeskill', 'employeephoto', 'workplace']


def get_permissions(codenames: list):
    return Permission.objects.filter(
        content_type__app_label__in=['employees', 'workplaces'],
        codename__in=codenames,
    )


class Command(BaseCommand):
    help = 'Создает группы «Смотритель» и «Администратор» с правами доступа'

    def handle(self, *args, **options):
        keeper, _ = Group.objects.get_or_create(name='Смотритель')
        keeper.permissions.set(get_permissions(KEEPER_PERMISSIONS))

        admin_codenames = [
            f'{action}_{model}'
            for model in ADMIN_MODELS
            for action in ['add', 'change', 'delete', 'view']
        ]
        admin, _ = Group.objects.get_or_create(name='Администратор')
        admin.permissions.set(get_permissions(admin_codenames))
        self.stdout.write('Группы «Смотритель» и «Администратор» созданы')
