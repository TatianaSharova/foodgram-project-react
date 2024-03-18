from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Класс переопределения базового user."""

    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'

    ROLE_CHOICES = (
        (ROLE_ADMIN, 'admin'),
        (ROLE_USER, 'user')
    )

    password = None
    first_name = models.CharField('first name', max_length=150, blank=False)
    last_name = models.CharField('last name', max_length=150, blank=False)
    role = models.CharField(
        choices=ROLE_CHOICES, default=ROLE_USER,
        max_length=6)
    email = models.EmailField('E-mail', blank=False)

    class Meta:
        ordering = ('id',)

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_user(self):
        return self.role == self.ROLE_USER
