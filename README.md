# Трекер задач сотрудников
Трекер задач сотрудников — это серверное приложение на Django REST Framework для управления задачами и распределения нагрузки между сотрудниками. Система позволяет руководителям отслеживать загруженность команды и находить "узкие места" в рабочих процессах.

🚀 Основные возможности
Управление сотрудниками: CRUD-операции для сотрудников с ролями "руководитель" и "сотрудник".

Управление задачами: Создание, назначение, обновление статуса задач с поддержкой подзадач и приоритетов.

Аналитика нагрузки: Специальные эндпоинты для анализа загруженности команды.

Автодокументация API: Полная OpenAPI-документация через Swagger UI и ReDoc.

Готовая контейнеризация: Запуск через Docker Compose.

🛠 Технологический стек
Бэкенд: Python 3.11, Django 4.2, Django REST Framework

База данных: PostgreSQL

Документация: drf-spectacular (Swagger/ReDoc)

Контейнеризация: Docker, Docker Compose

📦 Быстрый старт (с Docker)
Клонируйте репозиторий

bash
git clone <ваш-репозиторий>
cd task-tracker
Настройте переменные окружения

bash
cp .env.example .env
# Отредактируйте .env при необходимости
Запустите проект

bash
docker-compose up --build
Примените миграции и создайте суперпользователя (в новом терминале):

bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
# Следуйте инструкциям (используйте табельный номер 0001)
Откройте в браузере:

Приложение: http://localhost:8000

Админка: http://localhost:8000/admin

Документация API (Swagger): http://localhost:8000/api/docs

Документация API (ReDoc): http://localhost:8000/api/redoc

🔧 Ручная установка (без Docker)
Создайте виртуальное окружение и установите зависимости:

bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
Настройте базу данных PostgreSQL и обновите настройки в .env.

Выполните миграции:

bash
python manage.py migrate
Создайте суперпользователя:

bash
python manage.py createsuperuser
Запустите сервер:

bash
python manage.py runserver
📚 API Endpoints
GET /api/users/ - Список пользователей (только для руководителей)

POST /api/users/login/ - Аутентификация по табельному номеру

GET /api/tasks/ - CRUD для задач (с фильтрацией и поиском)

GET /api/busy-employees/ - Аналитика: самые загруженные сотрудники

GET /api/important-tasks/ - Аналитика: "заблокированные" задачи и кандидаты на выполнение

Полная документация доступна в Swagger UI после запуска проекта.

🧪 Тестирование
bash
# Запуск всех тестов
python manage.py test

# Запуск с покрытием
coverage run manage.py test
coverage report
Проект покрыт тестами более чем на 75% (модели, сериализаторы, API).

🔐 Модели данных
CustomUser: Кастомная модель пользователя с табельным номером вместо username

Task: Задачи с поддержкой подзадач, приоритетов (1-10), статусов и сроков выполнения

📁 Структура проекта

text

task-tracker/

├── config/              # Настройки Django

├── employees/           # Приложение "Сотрудники"

├── tasks/              # Приложение "Задачи"

├── docker-compose.yml  # Конфигурация Docker

├── Dockerfile          # Образ приложения

├── .env.example        # Шаблон переменных окружения
                        
└── requirements.txt    # Зависимости Python

🚀 Дальнейшее развитие
Интеграция с Telegram для уведомлений

Фронтенд на Vue.js/React

Фоновая обработка задач через Celery

Детальная система отчетов

📄 Лицензия
MIT