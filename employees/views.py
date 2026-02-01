from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser
from .serializers import (
    CustomUserSerializer,
    CustomUserCreateSerializer,
    CustomUserUpdateSerializer
)


class CustomUserViewSet(viewsets.ModelViewSet):
    swagger_tags = ['Пользователи']
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CustomUserUpdateSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'update', 'partial_update', 'destroy']:
            # Только руководители могут управлять пользователями
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        employee_id = request.data.get('employee_id')
        password = request.data.get('password')

        if not employee_id or not password:
            return Response(
                {'error': 'Необходимо указать табельный номер и пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=employee_id, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                serializer = self.get_serializer(user)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Аккаунт отключен'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Неверный табельный номер или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'message': 'Выход выполнен успешно'})
