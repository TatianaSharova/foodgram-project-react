from django.contrib import admin

from .models import Follow, Tag, Ingredient, Recipe


class RecipeIngredientInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 1


class RecipeTagInLine(admin.TabularInline):
    model = Recipe.tags.through
    extra = 1


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'following')
    search_fields = ('user', 'following')
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'text',
                    'pub_date', 'author')
    search_fields = ('name', 'author')
    inlines = (RecipeIngredientInLine, RecipeTagInLine)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = '-пусто-'
