from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Q, Subquery, OuterRef
from django.utils import timezone

from employees.serializers import BusyEmployeeSerializer
from tasks.models import Task
from employees.models import CustomUser
from tasks.serializers import (
    TaskSerializer, ImportantTaskResponseSerializer,
    PermissionErrorSerializer, AuthenticationErrorSerializer
)
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

class BusyEmployeesView(APIView):
    """
    Эндпоинт: Занятые сотрудники
    Возвращает список сотрудников и их задачи, отсортированный по количеству активных задач.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Список занятых сотрудников',
        description="""
        Возвращает список сотрудников, отсортированный по убыванию количества активных задач.
        Активной считается задача со статусом "new" или "in_progress".
        Для каждого сотрудника выводится общее число активных задач и их детальный список.
        """,
        responses={
            200: OpenApiResponse(
                response=BusyEmployeeSerializer(many=True),
                description='Список важных задач с потенциальными исполнителями.'
            ),
            401: OpenApiResponse(
                response=AuthenticationErrorSerializer,  # Используем ваш сериализатор
                description='Требуется аутентификация.'
            ),
            403: OpenApiResponse(
                response=PermissionErrorSerializer,      # Используем ваш сериализатор
                description='Доступ запрещен.'
            ),
        },
        tags=['Аналитика'],
    )
    def get(self, request):
        # Подсчет активных задач для каждого сотрудника (статус 'new' или 'in_progress')
        busy_employees = CustomUser.objects.filter(
            tasks__status__in=['new', 'in_progress']
        ).annotate(
            active_tasks_count=Count('tasks', filter=Q(tasks__status__in=['new', 'in_progress']))
        ).filter(
            active_tasks_count__gt=0
        ).order_by('-active_tasks_count')

        result = []
        for employee in busy_employees:
            active_tasks = employee.tasks.filter(status__in=['new', 'in_progress'])
            result.append({
                'employee_id': employee.employee_id,
                'full_name': employee.full_name,
                'position': employee.position,
                'active_tasks_count': employee.active_tasks_count,
                'tasks': TaskSerializer(active_tasks, many=True).data
            })

        return Response(result)


class ImportantTasksView(APIView):
    """
    Эндпоинт: Важные задачи
    1. Задачи, которые не взяты в работу, но от которых зависят другие задачи, взятые в работу.
    2. Поиск сотрудников, которые могут взять такие задачи.
    3. Возвращает список объектов: {Важная задача, Срок, [ФИО сотрудника]}
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Поиск важных задач',
        description="""
        Находит "заблокированные" задачи.

        **Критерий поиска:**
        1. Задача имеет статус **"Новая"** (не взята в работу).
        2. У задачи есть **минимум одна подзадача в статусе "В работе"**.

        **Подбор исполнителей:**
        Для каждой найденной задачи система предлагает потенциальных исполнителей:
        1. **Наименее загруженный сотрудник** на данный момент.
        2. **Сотрудник, выполняющий родительскую задачу** (если у него назначено не более чем на **2 активные задачи больше**, чем у наименее загруженного).

        **Ответ:** Список объектов, каждый из которых содержит задачу, её срок и массив подходящих сотрудников с указанием причины.
        """,
        responses={
            200: OpenApiResponse(
                response=ImportantTaskResponseSerializer(many=True),
                description='Список важных задач с потенциальными исполнителями.'
            ),
            401: OpenApiResponse(
                response=AuthenticationErrorSerializer,  # Используем ваш сериализатор
                description='Требуется аутентификация.'
            ),
            403: OpenApiResponse(
                response=PermissionErrorSerializer,      # Используем ваш сериализатор
                description='Доступ запрещен.'
            ),
        },
        tags=['Аналитика'],
    )
    def get(self, request):
        # 1. Находим задачи со статусом 'new', у которых есть подзадачи в статусе 'in_progress'
        important_tasks = Task.objects.filter(
            status='new',  # Не взяты в работу
            subtasks__status='in_progress'  # Имеют подзадачи в работе
        ).distinct()

        result = []

        for task in important_tasks:
            # 2. Находим подходящих сотрудников для этой задачи

            # Наименее загруженный сотрудник
            least_busy_employee = self._find_least_busy_employee()

            # Сотрудник, выполняющий родительскую задачу (если есть)
            parent_executor = None
            if task.parent_task and task.parent_task.executor:
                parent_executor = task.parent_task.executor

            # Список потенциальных исполнителей
            potential_executors = []

            if least_busy_employee:
                potential_executors.append({
                    'employee_id': least_busy_employee.employee_id,
                    'full_name': least_busy_employee.full_name,
                    'position': least_busy_employee.position,
                    'reason': 'Наименее загруженный сотрудник'
                })

            if parent_executor:
                # Проверяем условие: "назначено максимум на 2 задачи больше, чем у наименее загруженного сотрудника"
                least_busy_count = self._get_active_task_count(least_busy_employee) if least_busy_employee else 0
                parent_executor_count = self._get_active_task_count(parent_executor)

                if parent_executor_count <= least_busy_count + 2:
                    potential_executors.append({
                        'employee_id': parent_executor.employee_id,
                        'full_name': parent_executor.full_name,
                        'position': parent_executor.position,
                        'reason': 'Исполнитель родительской задачи'
                    })

            result.append({
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'priority': task.priority
                },
                'deadline': task.deadline,
                'potential_executors': potential_executors
            })

        return Response(result)

    def _get_active_task_count(self, employee):
        """Получить количество активных задач у сотрудника."""
        if not employee:
            return 0
        return Task.objects.filter(
            executor=employee,
            status__in=['new', 'in_progress']
        ).count()

    def _find_least_busy_employee(self):
        """Найти наименее загруженного сотрудника."""
        # Подсчитываем активные задачи для каждого сотрудника
        employees = CustomUser.objects.filter(
            role='employee',
            is_active=True
        ).annotate(
            active_tasks_count=Count('tasks', filter=Q(tasks__status__in=['new', 'in_progress']))
        ).order_by('active_tasks_count')

        return employees.first()
