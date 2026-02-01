from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер для модели CustomUser."""

    def create_user(self, employee_id, password=None, **extra_fields):
        if not employee_id:
            raise ValueError('The Employee ID must be set')

        user = self.model(employee_id=employee_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'manager')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(employee_id, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Руководитель'),
        ('employee', 'Сотрудник'),
    ]

    username = None
    first_name = None
    last_name = None

    employee_id = models.CharField(
        'Табельный номер',
        max_length=4,
        unique=True,
        validators=[
            MinLengthValidator(4),
            RegexValidator(r'^\d{4}$', 'Табельный номер должен состоять из 4 цифр')
        ],
        help_text='4-значный цифровой идентификатор сотрудника'
    )
    full_name = models.CharField('ФИО', max_length=255)
    position = models.CharField('Должность', max_length=100)
    role = models.CharField('Роль', max_length=10, choices=ROLE_CHOICES, default='employee')
    telegram_id = models.CharField('Telegram ID', max_length=100, blank=True)

    email = models.EmailField('Email', blank=True)

    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['full_name', 'position']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['employee_id']

    def __str__(self):
        return f'{self.employee_id} - {self.full_name}'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_employee(self):
        return self.role == 'employee'