from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from employees.views import CustomUserViewSet
from tasks.views import TaskViewSet
from tasks.special_views import BusyEmployeesView, ImportantTasksView

router = routers.DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('api/busy-employees/', BusyEmployeesView.as_view(), name='busy-employees'),
    path('api/important-tasks/', ImportantTasksView.as_view(), name='important-tasks'),
]
