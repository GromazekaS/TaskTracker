from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from time import sleep
from employees.models import CustomUser
from tasks.models import Task


class TaskModelTest(TestCase):
    """Тесты модели Task."""

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
            password='pass123'
        )

        self.employee2 = CustomUser.objects.create_user(
            employee_id='1002',
            full_name='Петров Петр',
            position='Техник',
            password='pass123'
        )

        # Создаем задачу
        self.task_data = {
            'title': 'Тестовая задача',
            'executor': self.employee1,
            'deadline': timezone.now() + timedelta(days=7),
            'priority': 5,
            'description': 'Описание тестовой задачи',
            'created_by': self.manager
        }

    def test_create_task(self):
        """Создание задачи."""
        task = Task.objects.create(**self.task_data)

        self.assertEqual(task.title, 'Тестовая задача')
        self.assertEqual(task.executor, self.employee1)
        self.assertEqual(task.priority, 5)
        self.assertEqual(task.status, 'new')
        self.assertEqual(task.created_by, self.manager)
        self.assertFalse(task.is_overdue)

    def test_priority_validation(self):
        """Валидация приоритета."""
        # Приоритет должен быть от 1 до 10
        self.task_data['priority'] = 0
        task = Task(**self.task_data)
        with self.assertRaises(ValidationError):
            task.full_clean()

        self.task_data['priority'] = 11
        task = Task(**self.task_data)
        with self.assertRaises(ValidationError):
            task.full_clean()

        # Корректные значения
        for priority in [1, 5, 10]:
            self.task_data['priority'] = priority
            task = Task(**self.task_data)
            try:
                task.full_clean()
            except ValidationError:
                self.fail(f'Priority {priority} should be valid')

    def test_deadline_validation(self):
        """Валидация срока выполнения."""
        # Дедлайн в прошлом должен вызывать ошибку
        past_deadline = timezone.now() - timedelta(days=1)
        self.task_data['deadline'] = past_deadline
        task = Task(**self.task_data)

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_subtask_validation(self):
        """Валидация вложенности подзадач."""
        # Создаем родительскую задачу
        parent_task = Task.objects.create(**self.task_data)

        # Создаем подзадачу
        subtask = Task.objects.create(
            title='Подзадача',
            parent_task=parent_task,
            executor=self.employee1,
            deadline=timezone.now() + timedelta(days=5),
            priority=3,
            description='Описание подзадачи',
            created_by=self.manager
        )

        # Попытка создать подзадачу для подзадачи (вложенность > 1 уровня)
        nested_subtask = Task(
            title='Вложенная подзадача',
            parent_task=subtask,
            executor=self.employee1,
            deadline=timezone.now() + timedelta(days=4),
            priority=2,
            created_by=self.manager
        )

        with self.assertRaises(ValidationError):
            nested_subtask.full_clean()

    def test_subtask_executor_validation(self):
        """Валидация исполнителя подзадачи."""
        # Создаем родительскую задачу
        parent_task = Task.objects.create(**self.task_data)

        # Подзадача с другим исполнителем должна вызвать ошибку
        subtask = Task(
            title='Подзадача',
            parent_task=parent_task,
            executor=self.employee2,  # Другой исполнитель!
            deadline=timezone.now() + timedelta(days=5),
            priority=3,
            created_by=self.manager
        )

        with self.assertRaises(ValidationError) as context:
            subtask.full_clean()

        self.assertIn('executor', str(context.exception))

    def test_is_overdue_property(self):
        """Тестирование свойства is_overdue."""
        # Просроченная задача
        overdue_task = Task.objects.create(
            title='Просроченная задача',
            executor=self.employee1,
            deadline=timezone.now() + timedelta(seconds=1),
            priority=5,
            status='in_progress',
            created_by=self.manager
        )
        sleep(2)
        self.assertTrue(overdue_task.is_overdue)

        # Непросроченная задача
        not_overdue_task = Task.objects.create(
            title='Непросроченная задача',
            executor=self.employee1,
            deadline=timezone.now() + timedelta(days=1),
            priority=5,
            status='in_progress',
            created_by=self.manager
        )
        self.assertFalse(not_overdue_task.is_overdue)

        # Завершенная задача не считается просроченной
        completed_task = Task.objects.create(
            title='Завершенная задача',
            executor=self.employee1,
            deadline=timezone.now() + timedelta(seconds=1),
            priority=5,
            status='completed',
            created_by=self.manager
        )
        sleep(2)
        self.assertFalse(completed_task.is_overdue)

    def test_has_subtasks_property(self):
        """Тестирование свойства has_subtasks."""
        task = Task.objects.create(**self.task_data)
        self.assertFalse(task.has_subtasks)

        # Добавляем подзадачу
        Task.objects.create(
            title='Подзадача',
            parent_task=task,
            executor=self.employee1,
            deadline=timezone.now() + timedelta(days=5),
            priority=3,
            created_by=self.manager
        )

        task.refresh_from_db()
        self.assertTrue(task.has_subtasks)