from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('employee_id', 'password')}),
        ('Персональная информация', {'fields': ('full_name', 'position', 'email', 'telegram_id')}),
        ('Роли и права', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('employee_id', 'full_name', 'position', 'password1', 'password2', 'role'),
        }),
    )

    list_display = ('employee_id', 'full_name', 'position', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('employee_id', 'full_name', 'email')
    ordering = ('employee_id',)
    filter_horizontal = ()