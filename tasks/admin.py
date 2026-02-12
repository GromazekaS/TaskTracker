from django.contrib import admin
from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'executor', 'status', 'priority', 'deadline', 'created_at')
    list_filter = ('status', 'priority', 'executor')
    search_fields = ('title', 'description')
    raw_id_fields = ('parent_task', 'executor', 'created_by')
    date_hierarchy = 'deadline'

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'parent_task')
        }),
        ('Исполнение', {
            'fields': ('executor', 'status', 'priority', 'deadline')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')
