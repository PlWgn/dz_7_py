from django.core.exceptions import ValidationError
from django.test import TestCase

from employees.models import EmployeeSkill, Skill, User

from .models import Workplace


class NeighborsValidatorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        backend = Skill.objects.create(
            name='Бэкенд', category=Skill.Category.DEVELOPER
        )
        frontend = Skill.objects.create(
            name='Фронтенд', category=Skill.Category.DEVELOPER
        )
        testing = Skill.objects.create(
            name='Тестирование', category=Skill.Category.TESTER
        )
        manager = Skill.objects.create(name='Управление проектами')
        cls.tester = cls.create_employee('tester', [testing])
        cls.backend = cls.create_employee('backend', [backend])
        cls.frontend = cls.create_employee('frontend', [frontend])
        cls.manager = cls.create_employee('manager', [manager])
        cls.second_tester = cls.create_employee('tester2', [testing])
        cls.fullstack_tester = cls.create_employee(
            'fullstack', [backend, testing]
        )

    @classmethod
    def create_employee(cls, username: str, skills: list):
        employee = User.objects.create_user(
            username=username, password='Pass12345!'
        )
        for skill in skills:
            EmployeeSkill.objects.create(
                employee=employee, skill=skill, level=5
            )
        return employee

    def setUp(self):
        # тестировщик сидит за 2 столом
        Workplace.objects.create(desk_number=2, employee=self.tester)

    def test_developer_next_to_tester(self):
        for employee in [self.backend, self.frontend]:
            for desk_number in [1, 3]:
                with self.subTest(
                    employee=employee.username, desk_number=desk_number
                ):
                    with self.assertRaises(ValidationError):
                        Workplace.objects.create(
                            desk_number=desk_number, employee=employee
                        )
        self.assertEqual(Workplace.objects.count(), 1)

    def test_tester_next_to_developer(self):
        Workplace.objects.create(desk_number=5, employee=self.backend)
        for desk_number in [4, 6]:
            with self.subTest(desk_number=desk_number):
                with self.assertRaises(ValidationError):
                    Workplace.objects.create(
                        desk_number=desk_number, employee=self.second_tester
                    )

    def test_developer_not_next_to_tester(self):
        Workplace.objects.create(desk_number=4, employee=self.backend)
        self.assertTrue(
            Workplace.objects.filter(
                desk_number=4, employee=self.backend
            ).exists()
        )

    def test_other_employees_next_to_tester(self):
        Workplace.objects.create(desk_number=1, employee=self.manager)
        Workplace.objects.create(desk_number=3, employee=self.second_tester)
        self.assertEqual(Workplace.objects.count(), 3)

    def test_developer_and_tester_in_one_person(self):
        with self.assertRaises(ValidationError):
            Workplace.objects.create(
                desk_number=3, employee=self.fullstack_tester
            )

    def test_move_to_desk_next_to_tester(self):
        workplace = Workplace.objects.create(
            desk_number=10, employee=self.backend
        )
        workplace.desk_number = 3
        with self.assertRaises(ValidationError):
            workplace.save()
        workplace.refresh_from_db()
        self.assertEqual(workplace.desk_number, 10)

    def test_empty_desk_next_to_tester(self):
        Workplace.objects.create(desk_number=3)
        self.assertEqual(Workplace.objects.count(), 2)

    def test_error_message(self):
        with self.assertRaisesMessage(
            ValidationError, 'за соседним столом №2'
        ):
            Workplace.objects.create(desk_number=1, employee=self.backend)
