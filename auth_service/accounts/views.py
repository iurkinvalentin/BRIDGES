from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, RegisterSerializer, ProfileUpdateSerializer, ProfileSerializer
from .models import Profile


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
