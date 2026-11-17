from datetime import date, timedelta
from http import HTTPStatus

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APITestCase

from employees.models import EmployeeSkill, Skill, User
from workplaces.models import Workplace


class EmployeeApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('create_roles', stdout=open('/dev/null', 'w'))
        cls.backend = Skill.objects.create(
            name='Бэкенд', category=Skill.Category.DEVELOPER
        )
        cls.testing = Skill.objects.create(
            name='Тестирование', category=Skill.Category.TESTER
        )
        cls.employees = []
        for i in range(15):
            employee = User.objects.create_user(
                username=f'user{i}',
                first_name=f'Имя{i}',
                hire_date=date.today() - timedelta(days=i * 100),
            )
            skill = cls.testing if i == 0 else cls.backend
            EmployeeSkill.objects.create(
                employee=employee, skill=skill, level=5
            )
            cls.employees.append(employee)
        cls.visitor = User.objects.create_user(
            'visitor', password='Pass12345!'
        )
        cls.keeper = User.objects.create_user('keeper', password='Pass12345!')
        cls.keeper.groups.add(Group.objects.get(name='Смотритель'))
        cls.admin = User.objects.create_user('boss', password='Pass12345!')
        cls.admin.groups.add(Group.objects.get(name='Администратор'))
        for desk_number in range(1, 6):
            Workplace.objects.create(desk_number=desk_number)
        Workplace.objects.filter(desk_number=1).update(
            employee=cls.employees[0]
        )
        cls.list_url = reverse('employee-list')
        cls.detail_url = reverse('employee-detail', args=[cls.employees[1].pk])
        cls.move_url = reverse('employee-move', args=[cls.employees[1].pk])

    def test_list_with_pagination(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data['count'], 18)
        self.assertEqual(len(response.data['results']), 10)

    def test_filter_by_skill_and_experience(self):
        response = self.client.get(self.list_url, {'skill': 'Тестирование'})
        self.assertEqual(
            [item['username'] for item in response.data['results']], ['user0']
        )
        response = self.client.get(
            self.list_url, {'skills': self.backend.id, 'min_experience': 1000}
        )
        self.assertEqual(response.data['count'], 5)
        response = self.client.get(self.list_url, {'max_experience': 150})
        self.assertEqual(response.data['count'], 5)

    def test_detail_needs_login(self):
        self.assertEqual(
            self.client.get(self.detail_url).status_code,
            HTTPStatus.UNAUTHORIZED,
        )
        self.client.force_authenticate(self.visitor)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('photos', response.data)

    def test_jwt_login(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'visitor', 'password': 'Pass12345!'},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}'
        )
        self.assertEqual(
            self.client.get(self.detail_url).status_code, HTTPStatus.OK
        )

    def test_crud_only_for_admin(self):
        data = {
            'username': 'new',
            'first_name': 'Новый',
            'skills': [{'skill': self.backend.id, 'level': 3}],
        }
        for user in [self.visitor, self.keeper]:
            with self.subTest(user=user.username):
                self.client.force_authenticate(user)
                self.assertEqual(
                    self.client.post(
                        self.list_url, data, format='json'
                    ).status_code,
                    HTTPStatus.FORBIDDEN,
                )
                self.assertEqual(
                    self.client.patch(
                        self.detail_url, {'first_name': 'X'}
                    ).status_code,
                    HTTPStatus.FORBIDDEN,
                )
                self.assertEqual(
                    self.client.delete(self.detail_url).status_code,
                    HTTPStatus.FORBIDDEN,
                )
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(response.data['skills'][0]['skill_name'], 'Бэкенд')
        response = self.client.patch(
            self.detail_url, {'first_name': 'Изменено'}
        )
        self.assertEqual(response.data['first_name'], 'Изменено')
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            HTTPStatus.NO_CONTENT,
        )

    def test_move_rights(self):
        self.client.force_authenticate(self.visitor)
        self.assertEqual(
            self.client.post(self.move_url, {'desk_number': 4}).status_code,
            HTTPStatus.FORBIDDEN,
        )
        for user, desk_number in [(self.keeper, 4), (self.admin, 5)]:
            with self.subTest(user=user.username):
                self.client.force_authenticate(user)
                response = self.client.post(
                    self.move_url, {'desk_number': desk_number}
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertEqual(response.data['desk_number'], desk_number)
        self.assertEqual(
            Workplace.objects.filter(employee=self.employees[1]).count(), 1
        )

    def test_move_checks_neighbors(self):
        self.client.force_authenticate(self.keeper)
        # за 1 столом сидит тестировщик, бэкендера за 2 посадить нельзя
        response = self.client.post(self.move_url, {'desk_number': 2})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        response = self.client.post(self.move_url, {'desk_number': 1})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
