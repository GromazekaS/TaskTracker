from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from employees.models import CustomUser


class CustomUserViewSetTest(APITestCase):
    """Тесты API для пользователей."""

    def setUp(self):
        # Создаем менеджера и сотрудника
        self.manager = CustomUser.objects.create_user(
            employee_id='0001',
            full_name='Менеджер',
            position='Руководитель',
            role='manager',
            password='manager123'
        )

        self.employee = CustomUser.objects.create_user(
            employee_id='1001',
            full_name='Сотрудник',
            position='Инженер',
            password='employee123'
        )

        self.client = APIClient()

    def test_login(self):
        """Тестирование входа в систему."""
        url = reverse('user-login')
        data = {
            'employee_id': '1001',
            'password': 'employee123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('employee_id', response.data)
        self.assertEqual(response.data['employee_id'], '1001')

    def test_login_invalid_credentials(self):
        """Тестирование входа с неверными учетными данными."""
        url = reverse('user-login')
        data = {
            'employee_id': '1001',
            'password': 'wrongpassword'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list_as_manager(self):
        """Менеджер может видеть список пользователей."""
        self.client.force_authenticate(user=self.manager)
        url = reverse('user-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # manager + employee

    def test_user_list_as_employee(self):
        """Сотрудник не может видеть список пользователей."""
        self.client.force_authenticate(user=self.employee)
        url = reverse('user-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_as_manager(self):
        """Менеджер может создавать пользователей."""
        self.client.force_authenticate(user=self.manager)
        url = reverse('user-list')

        data = {
            'employee_id': '1002',
            'full_name': 'Новый сотрудник',
            'position': 'Аналитик',
            'password': 'newpass123',
            'password2': 'newpass123',
            'role': 'employee'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 3)

    def test_create_user_as_employee(self):
        """Сотрудник не может создавать пользователей."""
        self.client.force_authenticate(user=self.employee)
        url = reverse('user-list')

        data = {
            'employee_id': '1002',
            'full_name': 'Новый сотрудник',
            'position': 'Аналитик',
            'password': 'newpass123',
            'password2': 'newpass123'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_current_user(self):
        """Получение информации о текущем пользователе."""
        self.client.force_authenticate(user=self.employee)
        url = reverse('user-me')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['employee_id'], '1001')
        self.assertEqual(response.data['full_name'], 'Сотрудник')