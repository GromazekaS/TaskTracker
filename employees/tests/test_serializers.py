from django.test import TestCase
from rest_framework.exceptions import ValidationError
from employees.models import CustomUser
from employees.serializers import (
    CustomUserSerializer,
    CustomUserCreateSerializer,
    CustomUserUpdateSerializer
)


class CustomUserSerializerTest(TestCase):
    """Тесты сериализаторов пользователей."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            employee_id='1001',
            full_name='Иванов Иван',
            position='Инженер',
            password='testpass123'
        )

    def test_user_serializer(self):
        """Тестирование CustomUserSerializer."""
        serializer = CustomUserSerializer(self.user)

        data = serializer.data
        self.assertEqual(data['employee_id'], '1001')
        self.assertEqual(data['full_name'], 'Иванов Иван')
        self.assertEqual(data['position'], 'Инженер')
        self.assertEqual(data['role'], 'employee')
        self.assertIn('date_joined', data)
        self.assertIn('last_login', data)
        self.assertNotIn('password', data)

    def test_user_create_serializer(self):
        """Тестирование создания пользователя."""
        data = {
            'employee_id': '1002',
            'full_name': 'Петров Петр',
            'position': 'Техник',
            'password': 'Password123',
            'password2': 'Password123',
            'role': 'employee'
        }

        serializer = CustomUserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.employee_id, '1002')
        self.assertTrue(user.check_password('Password123'))

    def test_user_create_serializer_password_mismatch(self):
        """Тестирование создания пользователя с несовпадающими паролями."""
        data = {
            'employee_id': '1002',
            'full_name': 'Петров Петр',
            'position': 'Техник',
            'password': 'Password123',
            'password2': 'DifferentPassword',
            'role': 'employee'
        }

        serializer = CustomUserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_user_update_serializer(self):
        """Тестирование обновления пользователя."""
        data = {
            'full_name': 'Иванов Иван Иванович',
            'position': 'Старший инженер',
            'email': 'ivanov@example.com',
            'telegram_id': '@ivanov'
        }

        serializer = CustomUserUpdateSerializer(self.user, data=data)
        self.assertTrue(serializer.is_valid())

        updated_user = serializer.save()
        self.assertEqual(updated_user.full_name, 'Иванов Иван Иванович')
        self.assertEqual(updated_user.position, 'Старший инженер')
        self.assertEqual(updated_user.email, 'ivanov@example.com')
        self.assertEqual(updated_user.telegram_id, '@ivanov')