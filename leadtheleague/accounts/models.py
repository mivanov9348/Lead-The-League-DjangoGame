import os
from django.contrib.auth.models import AbstractUser
from django.db import models

def avatar_upload_path(instance, filename):
    return os.path.join('avatars', filename)

class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'