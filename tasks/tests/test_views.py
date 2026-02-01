from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
from employees.models import CustomUser
from tasks.models import Task


class TaskViewSetTest(APITestCase):
    """Тесты API для задач."""

    def setUp(self):
        # Создаем пользователей
        self.manager = CustomUser.objects.create_user(
            employee_id='0001',
            full_name='Менеджер',
            position='Руководитель',
            role='manager',
            password='manager123'
        )

        self.employee1 = CustomUser.objects.create_user(
            employee_id='1001',
            full_name='Иванов Иван',
            position='Инженер',
            password='employee123'
        )

        self.employee2 = CustomUser.objects.create_user(
            employee_id='1002',
            full_name='Петров Петр',
            position='Техник',
            password='employee123'
        )

        # Создаем задачи
        self.task1 = Task.objects.create(
            title='Задача 1',
            executor=self.employee1,
            deadline=timezone.now() + timedelta(days=7),
            priority=5,
            description='Описание задачи 1',
            created_by=self.manager
        )

        self.task2 = Task.objects.create(
            title='Задача 2',
            executor=self.employee2,
            deadline=timezone.now() + timedelta(days=5),
            priority=8,
            status='in_progress',
            description='Описание задачи 2',
            created_by=self.manager
        )

        self.client = APIClient()

    def test_task_list_as_manager(self):
        """Менеджер видит все задачи."""
        self.client.force_authenticate(user=self.manager)
        url = reverse('task-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_task_list_as_employee(self):
        """Сотрудник видит только свои задачи."""
        self.client.force_authenticate(user=self.employee1)
        url = reverse('task-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Задача 1')

    def test_create_task_as_manager(self):
        """Менеджер может создавать задачи."""
        self.client.force_authenticate(user=self.manager)
        url = reverse('task-list')

        data = {
            'title': 'Новая задача',
            'executor': self.employee1.id,
            'deadline': (timezone.now() + timedelta(days=10)).isoformat(),
            'priority': 6,
            'description': 'Описание новой задачи',
            'status': 'new'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 3)

    def test_create_task_as_employee(self):
        """Сотрудник не может создавать задачи."""
        self.client.force_authenticate(user=self.employee1)
        url = reverse('task-list')

        data = {
            'title': 'Новая задача',
            'deadline': (timezone.now() + timedelta(days=10)).isoformat(),
            'priority': 6,
            'description': 'Описание новой задачи'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_task_status_as_executor(self):
        """Исполнитель может менять статус своей задачи."""
        self.client.force_authenticate(user=self.employee1)
        url = reverse('task-update-status', args=[self.task1.id])

        data = {'status': 'in_progress'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task1.refresh_from_db()
        self.assertEqual(self.task1.status, 'in_progress')

    def test_update_task_status_as_non_executor(self):
        """Сотрудник не может менять статус чужой задачи."""
        self.client.force_authenticate(user=self.employee1)
        url = reverse('task-update-status', args=[self.task2.id])  # Задача employee2

        data = {'status': 'completed'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_tasks_endpoint(self):
        """Тестирование эндпоинта /api/tasks/my_tasks/."""
        self.client.force_authenticate(user=self.employee1)
        url = reverse('task-my-tasks')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Задача 1')

    def test_available_tasks_endpoint(self):
        """Тестирование эндпоинта /api/tasks/available_tasks/."""
        # Создаем задачу без исполнителя
        Task.objects.create(
            title='Свободная задача',
            deadline=timezone.now() + timedelta(days=7),
            priority=5,
            description='Задача без исполнителя',
            created_by=self.manager
        )

        self.client.force_authenticate(user=self.employee1)
        url = reverse('task-available-tasks')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Свободная задача')