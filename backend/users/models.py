from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    '''Класс переопределения базового user.'''

    password = models.CharField('password', max_length=150, default=None)
    first_name = models.CharField('first name', max_length=150)
    last_name = models.CharField('last name', max_length=150)
    email = models.EmailField('E-mail', max_length=254, unique=True)

    class Meta:
        ordering = ('id',)
