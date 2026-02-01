from django.core.management.base import BaseCommand
from employees.models import CustomUser
from tasks.models import Task
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Создание тестовых данных'

    def handle(self, *args, **kwargs):
        # Создаем суперпользователя
        admin, created = CustomUser.objects.get_or_create(
            employee_id='0001',
            defaults={
                'full_name': 'Администратор',
                'position': 'Руководитель',
                'role': 'manager',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь 0001'))

        # Создаем сотрудников
        employees_data = [
            {'employee_id': '1001', 'full_name': 'Иванов Иван', 'position': 'Инженер'},
            {'employee_id': '1002', 'full_name': 'Петров Петр', 'position': 'Техник'},
            {'employee_id': '1003', 'full_name': 'Сидорова Анна', 'position': 'Аналитик'},
        ]

        for emp_data in employees_data:
            emp, created = CustomUser.objects.get_or_create(
                employee_id=emp_data['employee_id'],
                defaults={**emp_data, 'role': 'employee'}
            )
            if created:
                emp.set_password('pass123')
                emp.save()
                self.stdout.write(self.style.SUCCESS(f'Создан сотрудник {emp.employee_id}'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные созданы'))
