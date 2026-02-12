from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta
from employees.models import CustomUser
from tasks.models import Task


class SpecialEndpointsTest(APITestCase):
    """Тесты специальных эндпоинтов."""

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

        self.employee3 = CustomUser.objects.create_user(
            employee_id='1003',
            full_name='Сидоров Алексей',
            position='Аналитик',
            password='employee123'
        )

        # Создаем задачи для тестирования занятости
        now = timezone.now()

        # Задачи для employee1
        for i in range(3):
            Task.objects.create(
                title=f'Задача {i + 1} для сотрудника 1',
                executor=self.employee1,
                deadline=now + timedelta(days=i + 1),
                priority=5,
                status='in_progress',
                created_by=self.manager
            )

        # Задачи для employee2
        for i in range(2):
            Task.objects.create(
                title=f'Задача {i + 1} для сотрудника 2',
                executor=self.employee2,
                deadline=now + timedelta(days=i + 2),
                priority=6,
                status='new',
                created_by=self.manager
            )

        # Создаем важную задачу (не взята в работу, но имеет подзадачу в работе)
        self.important_task = Task.objects.create(
            title='Важная задача',
            executor=self.employee1,
            deadline=now + timedelta(days=10),
            priority=9,
            status='new',
            created_by=self.manager
        )

        # Подзадача в работе
        Task.objects.create(
            title='Подзадача важной задачи',
            parent_task=self.important_task,
            executor=self.employee1,
            deadline=now + timedelta(days=5),
            priority=8,
            status='in_progress',
            created_by=self.manager
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.manager)

    def test_busy_employees_endpoint(self):
        """Тестирование эндпоинта /api/busy-employees/."""
        url = reverse('busy-employees')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Должны быть 2 занятых сотрудника
        self.assertEqual(len(response.data), 2)

        # Проверяем порядок (по убыванию количества задач)
        self.assertEqual(response.data[0]['employee_id'], '1001')  # 3 задачи
        self.assertEqual(response.data[0]['active_tasks_count'], 5)

        self.assertEqual(response.data[1]['employee_id'], '1002')  # 2 задачи
        self.assertEqual(response.data[1]['active_tasks_count'], 2)

        # Проверяем структуру ответа
        employee_data = response.data[0]
        self.assertIn('employee_id', employee_data)
        self.assertIn('full_name', employee_data)
        self.assertIn('position', employee_data)
        self.assertIn('active_tasks_count', employee_data)
        self.assertIn('tasks', employee_data)

    def test_important_tasks_endpoint(self):
        """Тестирование эндпоинта /api/important-tasks/."""
        url = reverse('important-tasks')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Должна быть одна важная задача
        self.assertEqual(len(response.data), 1)

        task_data = response.data[0]
        self.assertIn('task', task_data)
        self.assertIn('deadline', task_data)
        self.assertIn('potential_executors', task_data)

        self.assertEqual(task_data['task']['title'], 'Важная задача')

        # Проверяем потенциальных исполнителей
        potential_executors = task_data['potential_executors']
        self.assertGreater(len(potential_executors), 0)

        # Должен быть наименее загруженный сотрудник
        least_busy_found = any(
            exec['reason'] == 'Наименее загруженный сотрудник'
            for exec in potential_executors
        )
        self.assertTrue(least_busy_found)

    def test_important_tasks_no_results(self):
        """Тестирование эндпоинта, когда важных задач нет."""
        # Удаляем важную задачу
        self.important_task.delete()

        url = reverse('important-tasks')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_authentication_required(self):
        """Тестирование требований прав менеджера."""
        self.client.logout()

        urls = [
            reverse('busy-employees'),
            reverse('important-tasks'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
