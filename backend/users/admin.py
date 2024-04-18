from django.contrib import admin

from .models import User
from recipes.constans import EMPTY_VALUE


@admin.register(User)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name',
                    'last_name', 'email', 'date_joined')
    list_filter = ('username', 'email',)
    search_fields = ('email', 'username')
    empty_value_display = EMPTY_VALUE
