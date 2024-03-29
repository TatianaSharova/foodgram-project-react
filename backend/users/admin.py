from django.contrib import admin

from .models import User


@admin.register(User)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email')
    search_fields = ('email', 'username')
    empty_value_display = '-пусто-'
