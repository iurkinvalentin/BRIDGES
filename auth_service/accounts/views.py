from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, RegisterSerializer, ProfileUpdateSerializer, ProfileSerializer, ConnectionsSerializer
from .models import Profile, Connections, CustomUser
from django.db.models import Q


class LoginView(APIView):
    """Вью для авторизации пользователя"""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Обработка POST запроса для авторизации"""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']  # Добавьте возврат пользователя в LoginSerializer

            # Генерация JWT токенов для пользователя
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            # Возвращаем access и refresh токены
            return Response({
                'refresh': str(refresh),
                'access': str(access),
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Вью для выхода пользователя"""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """Обработка POST запроса для выхода"""
        try:
            # Получаем refresh токен из запроса
            refresh_token = request.data.get("refresh_token")
            if refresh_token is None:
                return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Преобразуем его в объект RefreshToken и добавляем в черный список
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(generics.CreateAPIView):
    """Представление для регистрации пользователей"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """Создание пользователя"""
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерация JWT токенов для нового пользователя
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

        # Возвращаем данные о пользователе и токены
        return Response({
            'user': RegisterSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)


class DeleteView(APIView):
    """Представление для удаления пользователя"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        """Удаление пользователя"""
        user = request.user
        user.delete()

        return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """Представление для редактирования профиля и пользователя"""
    serializer_class = ProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Получаем профиль текущего пользователя или создаем новый"""
        user = self.request.user
        if not hasattr(user, 'profile'):
            # Создаем профиль, если его нет
            Profile.objects.create(user=user)
        return user.profile
    

class ProfileDetailView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile = self.request.user.profile
        profile.update_online_status()  # Обновляем статус перед возвратом профиля
        return profile


class ContactManagementView(APIView):
    """Управление запросами в контакты: отправка, подтверждение и удаление"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Отправить запрос на добавление в контакты"""
        from_user = request.user
        to_user_id = request.data.get('to_user_id')

        try:
            to_user = CustomUser.objects.get(id=to_user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if Connections.objects.filter(from_user=from_user, to_user=to_user).exists():
            return Response({"detail": "Request already sent"}, status=status.HTTP_400_BAD_REQUEST)

        connection = Connections.objects.create(from_user=from_user, to_user=to_user)
        return Response(ConnectionsSerializer(connection).data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        """Подтвердить запрос на добавление в контакты"""
        connection_id = kwargs.get('pk')
        try:
            connection = Connections.objects.get(id=connection_id, to_user=request.user, is_confirmed=False)
        except Connections.DoesNotExist:
            return Response({"detail": "Request not found or already confirmed"}, status=status.HTTP_404_NOT_FOUND)

        connection.is_confirmed = True
        connection.save()
        return Response(ConnectionsSerializer(connection).data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """Удалить контакт или отклонить запрос"""
        connection_id = kwargs.get('pk')
        try:
            connection = Connections.objects.get(id=connection_id)
            if request.user != connection.to_user and request.user != connection.from_user:
                return Response({"detail": "Not allowed"}, status=status.HTTP_403_FORBIDDEN)
        except Connections.DoesNotExist:
            return Response({"detail": "Connection not found"}, status=status.HTTP_404_NOT_FOUND)

        connection.delete()
        return Response({"detail": "Connection removed"}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        """Получить список всех подтвержденных контактов"""
        user = request.user
        # Получаем все подтвержденные связи, где текущий пользователь участвует как from_user или to_user
        confirmed_connections = Connections.objects.filter(
            Q(from_user=user) | Q(to_user=user),
            is_confirmed=True
        )

        serializer = ConnectionsSerializer(confirmed_connections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
