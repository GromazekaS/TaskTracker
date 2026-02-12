from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from employees.views import CustomUserViewSet
from tasks.views import TaskViewSet
from tasks.special_views import BusyEmployeesView, ImportantTasksView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


router = routers.DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('api/busy-employees/', BusyEmployeesView.as_view(), name='busy-employees'),
    path('api/important-tasks/', ImportantTasksView.as_view(), name='important-tasks'),

    # Маршруты для документации
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # Скачивание схемы OpenAPI
    # Swagger UI: http://127.0.0.1:8000/api/docs/
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ReDoc: http://127.0.0.1:8000/api/redoc/
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
