from django.contrib import admin

from .constans import EMPTY_VALUE, MIN_NUM
from .models import (Cart, Favorite, Follow, Ingredient, IngredientRecipe,
                     Recipe, Tag)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    autocomplete_fields = ('ingredient',)
    extra = MIN_NUM
    min_num = MIN_NUM


class RecipeTagInLine(admin.TabularInline):
    model = Recipe.tags.through
    autocomplete_fields = ('tag',)
    extra = MIN_NUM
    min_num = MIN_NUM


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'following')
    search_fields = ('user__username', 'following__username')
    empty_value_display = EMPTY_VALUE


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    empty_value_display = EMPTY_VALUE


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInline, RecipeTagInLine)
    list_display = ('id', 'name', 'text', 'pub_date',
                    'author', 'cooking_time', 'display_tags',
                    'favorites_count', 'display_ingredients')
    search_fields = ('name', 'author__username')
    list_filter = ('name', 'author', 'tags')
    empty_value_display = EMPTY_VALUE

    @admin.display(description='Количество добавлений в избранное')
    def favorites_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='Теги')
    def display_tags(self, recipe):
        return ', '.join([tags.name for tags in recipe.tags.all()])

    @admin.display(description='Ингредиенты')
    def display_ingredients(self, recipe):
        return ', '.join([
            ingredients.name for ingredients in recipe.ingredients.all()])


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInline,)
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = EMPTY_VALUE


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'recipe')
    list_filter = ('author', 'recipe')
    search_fields = ('author', 'recipe')
    empty_value_display = EMPTY_VALUE


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'recipe')
    list_filter = ('author', 'recipe')
    search_fields = ('author',)
    empty_value_display = EMPTY_VALUE
