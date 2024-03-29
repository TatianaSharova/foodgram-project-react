from django.db import models
from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from .validators import validate_color

User = get_user_model()

MINIMUM = 1


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название тега',
        unique=True
    )
    color = ColorField(
        format='hex',
        unique=True,
        max_length=7,
        verbose_name='Цвет в HEX'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Слаг',
        validators=[
            validate_color,
        ]
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('id',)
    
    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Название ингредиента',
        db_index=True
    )
    measurement_unit = models.CharField(
        max_length=20,
        verbose_name='Единица измерения')
    
    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('id',)
    
    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название рецепта'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes',
    )
    image = models.ImageField(
        upload_to='recipes/images/'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[MinValueValidator(
            MINIMUM, 'Время приготовления не может быть меньше 1 минуты!'
        )],
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes')
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_name_recipe')]
    
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


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(
            MINIMUM, 'Количество не может быть меньше 1!'
        )]
    )

    class Meta:
        ordering = ('id',)
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
        help_text='Текущий пользователь')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following',
        help_text='Подписаться на этого пользователя')

    class Meta:
        ordering = ('id',)
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
        ordering = ('id',)
        verbose_name = 'Список покупок'
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
        ordering = ('id',)
        verbose_name = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'author'],
                name='unique_favorite')]
    
    def __str__(self):
        return f'{self.author} добавил {self.recipe} в избранное.'
