from rest_framework import serializers
from django.utils import timezone
from .models import Task
from employees.models import CustomUser


class TaskSerializer(serializers.ModelSerializer):
    executor_info = serializers.SerializerMethodField()
    parent_task_title = serializers.CharField(source='parent_task.title', read_only=True)
    created_by_info = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    has_subtasks = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'parent_task', 'parent_task_title',
            'executor', 'executor_info', 'deadline', 'status',
            'priority', 'description', 'created_at', 'updated_at',
            'created_by', 'created_by_info', 'is_overdue', 'has_subtasks'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_executor_info(self, obj) -> dict | None:
        if obj.executor:
            return {
                'employee_id': obj.executor.employee_id,
                'full_name': obj.executor.full_name,
                'position': obj.executor.position
            }
        return None

    def get_created_by_info(self, obj) -> dict | None:
        if obj.created_by:
            return {
                'employee_id': obj.created_by.employee_id,
                'full_name': obj.created_by.full_name
            }
        return None

    def validate_deadline(self, value):
        if value < timezone.now():
            raise serializers.ValidationError('Срок выполнения не может быть в прошлом')
        return value

    def validate_priority(self, value):
        if not 1 <= value <= 10:
            raise serializers.ValidationError('Приоритет должен быть от 1 до 10')
        return value

    def validate(self, data):
        # Проверка вложенности
        parent_task = data.get('parent_task')
        if parent_task and parent_task.parent_task:
            raise serializers.ValidationError({
                'parent_task': 'Подзадачи не могут иметь свои подзадачи'
            })

        # Проверка исполнителя подзадачи
        if parent_task and 'executor' in data:
            if parent_task.executor and data['executor'] != parent_task.executor:
                raise serializers.ValidationError({
                    'executor': 'Подзадача должна быть назначена тому же исполнителю, что и родительская задача'
                })

        return data


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'title', 'parent_task', 'executor', 'deadline',
            'priority', 'description', 'status'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['status']

    def validate_status(self, value):
        user = self.context.get('request').user
        task = self.instance

        # Только исполнитель или руководитель может менять статус
        if not (user.is_manager or user == task.executor):
            raise serializers.ValidationError('Только исполнитель или руководитель может менять статус задачи')

        return value

class PotentialExecutorSerializer(serializers.Serializer):
    employee_id = serializers.CharField()
    full_name = serializers.CharField()
    position = serializers.CharField()
    reason = serializers.CharField()  # Например, 'Наименее загруженный сотрудник'

# Сериализатор для краткой информации о задаче
class ImportantTaskShortSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    priority = serializers.IntegerField()

# Основной сериализатор для элемента ответа
class ImportantTaskResponseSerializer(serializers.Serializer):
    task = ImportantTaskShortSerializer()
    deadline = serializers.DateTimeField()
    potential_executors = PotentialExecutorSerializer(many=True)

class ErrorDetailSerializer(serializers.Serializer):
    """Сериализатор для стандартного формата ошибок DRF (detail)."""
    detail = serializers.CharField()

class AuthenticationErrorSerializer(serializers.Serializer):
    """Сериализатор для ошибок аутентификации 401."""
    # Для Basic/Session аутентификации DRF может возвращать 'detail'
    # Но часто для 401 также может требоваться заголовок WWW-Authenticate
    detail = serializers.CharField(default='Учетные данные не были предоставлены.')

class PermissionErrorSerializer(serializers.Serializer):
    """Сериализатор для ошибок доступа 403."""
    detail = serializers.CharField(default='У вас недостаточно прав для выполнения этого действия.')
