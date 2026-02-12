from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from .models import Task
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskStatusUpdateSerializer
)


class TaskViewSet(viewsets.ModelViewSet):
    swagger_tags = ['Задачи'] # Не работает
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['deadline', 'priority', 'created_at', 'updated_at']
    ordering = ['-priority', 'deadline']

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()

        # Фильтрация в зависимости от роли
        if user.is_employee and not user.is_manager:
            # Сотрудник видит только свои задачи
            queryset = queryset.filter(executor=user)

        # Фильтр по статусу
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтр по приоритету
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        # Фильтр по просроченным
        overdue = self.request.query_params.get('overdue')
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(
                deadline__lt=timezone.now(),
                status__in=['new', 'in_progress']
            )

        return queryset.select_related('executor', 'parent_task', 'created_by')

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'update_status':
            return TaskStatusUpdateSerializer
        return TaskSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            # Только руководители могут создавать и удалять задачи
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Задачи текущего пользователя."""
        user = request.user
        tasks = Task.objects.filter(executor=user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available_tasks(self, request):
        """Свободные задачи (без исполнителя)."""
        tasks = Task.objects.filter(
            executor=None,
            status='new'
        ).exclude(parent_task__isnull=False)  # Исключаем подзадачи
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
