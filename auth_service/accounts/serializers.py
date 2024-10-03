from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, Profile, Connection
from django.core.validators import RegexValidator
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, required=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        # Аутентификация пользователя
        user = authenticate(username=username, password=password)

        if user and user.is_active:
            # Если аутентификация успешна, возвращаем пользователя
            data['user'] = user
            return data
        raise serializers.ValidationError("Неверные учетные данные или учетная запись не активна.")
    
    def create(self, validated_data):
        # Генерация JWT токенов
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""
    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        max_length=150,
        validators=[RegexValidator(r'^[\w.@+-]+$')],
        required=True
    )
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(
        write_only=True, required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        """Создание нового пользователя"""
        try:
            # Создание пользователя с хэшированием пароля
            user = CustomUser.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                password=validated_data['password']  # Пароль будет автоматически хэширован
            )
            return user
        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "username": "Пользователь с такими данными уже существует"
                }
            )


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')


class ProfileUpdateSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile
        fields = ('user', 'status_message', 'bio', 'avatar', 'birthday', 'is_online', 'last_seen')
    
    def update(self, instance, validated_data):
        # Извлечение данных пользователя
        user_data = validated_data.pop('user', None)
        # Обновляем данные профиля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Обновляем данные пользователя, если они были переданы
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        return instance


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class FriendshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = ('from_user', 'to_user', 'created')