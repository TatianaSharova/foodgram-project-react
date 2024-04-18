from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from .constans import (HEX_LENGTH, INGREDIENT_NAME_LEN, MAX_LENGTH,
                       MEASURE_UNIT_LEN, MIN_NUM)
from .validators import validate_color

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название тега',
        unique=True
    )
    color = ColorField(
        format='hex',
        unique=True,
        max_length=HEX_LENGTH,
        verbose_name='Цвет в HEX'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH,
        unique=True,
        verbose_name='Слаг',
        validators=[
            validate_color,
        ]
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_NAME_LEN,
        verbose_name='Название ингредиента',
        db_index=True
    )
    measurement_unit = models.CharField(
        max_length=MEASURE_UNIT_LEN,
        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название рецепта'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.IntegerField(
        validators=[
            MinValueValidator(
                MIN_NUM, f'Минимальное время приготовления {MIN_NUM} мин.'),
        ],
        verbose_name='Время приготовления в минутах'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты')
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        through='TagRecipe')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тэг',)
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Тэг для рецепта'
        verbose_name_plural = 'Тэги для рецептов'
        constraints = (
            models.UniqueConstraint(
                fields=('tag', 'recipe'),
                name='unique_tag'
            ),
        )

    def __str__(self):
        return f'Для {self.recipe} выбран тэг: {self.tag}'


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')
    amount = models.IntegerField(
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                MIN_NUM, f'Минимальное количество {MIN_NUM}'),
        ],
    )

    class Meta:
        ordering = ('recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient'
            ),
        )
        verbose_name = 'Ингредиенты для рецепта'
        verbose_name_plural = 'Ингредиенты для рецептов'

    def __str__(self):
        return f'Для {self.recipe} нужно {self.amount} {self.ingredient}.'


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower',
        help_text='Текущий пользователь',
        verbose_name='Подписчик')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following',
        help_text='Подписаться на этого пользователя',
        verbose_name='Пользователь')

    class Meta:
        ordering = ('user',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='prevent_self_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.following}.'


class Cart(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        ordering = ('author',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'author'],
                name='unique_recipe_in_cart')]

    def __str__(self):
        return f'{self.author} добавил в список покупок {self.recipe}.'


class Favorite(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        ordering = ('author',)
        verbose_name = 'Избранные рецепты'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'author'],
                name='unique_favorite')]

    def __str__(self):
        return f'{self.author} добавил {self.recipe} в избранное.'
