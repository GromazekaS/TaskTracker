from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from employees.models import CustomUser
from tasks.models import Task


class CustomUserModelTest(TestCase):
    """Тесты модели CustomUser."""

    def setUp(self):
        self.user_data = {
            'employee_id': '1001',
            'full_name': 'Иванов Иван Иванович',
            'position': 'Инженер',
            'password': 'testpass123'
        }

    def test_create_user(self):
        """Создание обычного пользователя."""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertEqual(user.employee_id, '1001')
        self.assertEqual(user.full_name, 'Иванов Иван Иванович')
        self.assertEqual(user.position, 'Инженер')
        self.assertEqual(user.role, 'employee')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Создание суперпользователя."""
        superuser = CustomUser.objects.create_superuser(
            employee_id='0001',
            full_name='Администратор',
            position='Руководитель',
            password='admin123'
        )
        self.assertEqual(superuser.employee_id, '0001')
        self.assertEqual(superuser.role, 'manager')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_employee_id_validation(self):
        """Валидация табельного номера."""
        # Должен состоять из 4 цифр
        with self.assertRaises(ValidationError):
            user = CustomUser(
                employee_id='123',
                full_name='Тест',
                position='Тест'
            )
            user.full_clean()

        with self.assertRaises(ValidationError):
            user = CustomUser(
                employee_id='12345',
                full_name='Тест',
                position='Тест'
            )
            user.full_clean()

        with self.assertRaises(ValidationError):
            user = CustomUser(
                employee_id='abcd',
                full_name='Тест',
                position='Тест'
            )
            user.full_clean()

    def test_unique_employee_id(self):
        """Табельный номер должен быть уникальным."""
        CustomUser.objects.create_user(
            employee_id='1001',
            full_name='Иванов',
            position='Инженер',
            password='pass123'
        )

        with self.assertRaises(Exception):
            CustomUser.objects.create_user(
                employee_id='1001',
                full_name='Петров',
                position='Техник',
                password='pass123'
            )

    def test_user_properties(self):
        """Тестирование свойств пользователя."""
        user = CustomUser.objects.create_user(**self.user_data)
        self.assertTrue(user.is_employee)
        self.assertFalse(user.is_manager)

        user.role = 'manager'
        self.assertFalse(user.is_employee)
        self.assertTrue(user.is_manager)