from django.contrib.auth.models import AbstractUser
from django.db import models

from recipes.constans import EMAIL_LENGTH, USER_MAX_LENGTH


class User(AbstractUser):
    '''Класс переопределения базового user.'''

    password = models.CharField('Пароль', default=None,
                                max_length=USER_MAX_LENGTH)
    first_name = models.CharField('Имя', max_length=USER_MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=USER_MAX_LENGTH)
    email = models.EmailField('E-mail', max_length=EMAIL_LENGTH, unique=True)

    class Meta:
        ordering = ('-date_joined',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
