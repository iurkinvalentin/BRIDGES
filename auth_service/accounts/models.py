from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    # Добавьте дополнительные поля, если необходимо
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.username