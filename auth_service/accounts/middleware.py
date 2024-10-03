import datetime
from django.utils import timezone


class UpdateLastStatusMiddleware:
    """
    Middleware для обновления last_seen и is_online пользователя при каждом запросе.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Проверяем, авторизован ли пользователь
        if request.user.is_authenticated:
            profile = request.user.profile
            profile.last_seen = timezone.now()
            profile.is_online = True  # Пользователь считается онлайн при каждом запросе
            profile.save()

        return response