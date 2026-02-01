from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings


class Task(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершена'),
    ]

    title = models.CharField('Название', max_length=255)
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='subtasks',
        verbose_name='Родительская задача',
        null=True,
        blank=True
    )
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='tasks',
        verbose_name='Исполнитель',
        null=True,
        blank=True
    )
    deadline = models.DateTimeField('Срок выполнения')
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    priority = models.IntegerField(
        'Приоритет',
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Целое число от 1 (низкий) до 10 (высокий)'
    )
    description = models.TextField('Описание', blank=True)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_tasks',
        verbose_name='Создатель',
        null=True
    )

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-priority', 'deadline']
        indexes = [
            models.Index(fields=['status', 'deadline']),
            models.Index(fields=['executor', 'status']),
        ]

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    def clean(self):
        errors = {}

        if self.deadline and self.deadline < timezone.now():
            errors['deadline'] = 'Срок выполнения не может быть в прошлом'

        if self.parent_task and self.parent_task.parent_task:
            errors['parent_task'] = 'Подзадачи не могут иметь свои подзадачи'

        if self.parent_task and self.executor:
            if self.parent_task.executor != self.executor:
                errors['executor'] = 'Подзадача должна быть назначена тому же исполнителю, что и родительская задача'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if not self.deadline:
            return False
        return self.status != 'completed' and timezone.now() > self.deadline

    @property
    def has_subtasks(self):
        return self.subtasks.exists()

    @property
    def all_subtasks(self):
        return self.subtasks.all()

    @property
    def active_subtasks(self):
        return self.subtasks.exclude(status='completed')
