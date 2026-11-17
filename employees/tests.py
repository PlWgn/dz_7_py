import shutil
import tempfile
from datetime import date, timedelta
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from workplaces.models import Workplace

from .models import EmployeePhoto, EmployeeSkill, Skill, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp()

# самая маленькая картинка gif 1x1
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class EmployeePagesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.skill = Skill.objects.create(
            name='Бэкенд', category=Skill.Category.DEVELOPER
        )
        cls.employees = []
        for i in range(12):
            employee = User.objects.create_user(
                username=f'user{i}',
                password='Pass12345!',
                first_name=f'Имя{i}',
                last_name=f'Фамилия{i}',
                gender=User.Gender.MALE,
                hire_date=date.today() - timedelta(days=i * 10),
            )
            EmployeeSkill.objects.create(
                employee=employee, skill=cls.skill, level=i % 10 + 1
            )
            cls.employees.append(employee)
        cls.employee = cls.employees[0]
        for order in [2, 1]:
            EmployeePhoto.objects.create(
                employee=cls.employee,
                image=SimpleUploadedFile(
                    f'photo{order}.gif', SMALL_GIF, content_type='image/gif'
                ),
                order=order,
            )
        Workplace.objects.create(desk_number=7, employee=cls.employee)
        cls.admin = User.objects.create_superuser(
            'admin', 'admin@mail.ru', 'Adm1nPass!'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client.force_login(self.employee)

    def test_index_page(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'employees/index.html')
        self.assertEqual(response.context['employees_count'], 12)
        employees = list(response.context['employees'])
        # 4 последних по дате приёма
        self.assertEqual(employees, self.employees[:4])

    def test_index_page_for_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_card_content(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Имя0 Фамилия0')
        self.assertContains(response, 'Бэкенд')
        self.assertContains(response, 'Стаж в компании: 10 дн.')
        self.assertContains(response, 'photo1')

    def test_employee_list_page(self):
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'employees/employee_list.html')
        self.assertTemplateUsed(response, 'employees/includes/card.html')
        self.assertEqual(len(response.context['employees']), 10)
        self.assertNotIn(self.admin, response.context['employees'])

    def test_employee_list_second_page(self):
        response = self.client.get(reverse('employee_list'), {'page': 2})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['employees']), 2)

    def test_employee_list_for_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_detail_page_for_authorized(self):
        response = self.client.get(
            reverse('employee_detail', args=[self.employee.pk])
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'employees/employee_detail.html')

    def test_detail_page_redirects_anonymous(self):
        self.client.logout()
        url = reverse('employee_detail', args=[self.employee.pk])
        response = self.client.get(url)
        self.assertRedirects(response, f'{reverse("login")}?next={url}')

    def test_detail_page_of_other_employee(self):
        response = self.client.get(
            reverse('employee_detail', args=[self.employees[5].pk])
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context['employee'], self.employees[5])

    def test_detail_page_not_found(self):
        for pk in [self.admin.pk, 9999]:
            with self.subTest(pk=pk):
                response = self.client.get(
                    reverse('employee_detail', args=[pk])
                )
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_detail_page_context(self):
        response = self.client.get(
            reverse('employee_detail', args=[self.employee.pk])
        )
        self.assertEqual(response.context['employee'], self.employee)
        self.assertEqual(response.context['main_photo'].order, 1)
        self.assertEqual(
            [photo.order for photo in response.context['gallery']], [2]
        )
        self.assertContains(response, 'Пол: Мужской')
        self.assertContains(response, 'Бэкенд: 1 из 10')
        self.assertContains(response, 'Номер стола: 7')
        self.assertContains(response, 'Стаж в компании: 0 дн.')

    def test_login_page(self):
        self.client.logout()
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
