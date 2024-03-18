from django.db import models
from colorfield.fields import ColorField
from django.contrib.auth import get_user_model

User = get_user_model()


class Tags(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Название тега'
    )
    color = ColorField(
        format='hexa',
        unique=True,
        max_length=8,
        verbose_name='Цвет в HEX'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('id',)
    
    def __str__(self):
        return self.name


class Ingredients(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Название ингредиента'
    )
    measure = models.CharField(
        max_length=20,
        verbose_name='Единица измерения')
    
    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('id',)
    
    def __str__(self):
        return self.name


class Recipes(models.Model):
    name = models.CharField(
        max_length=64,
        verbose_name='Название рецепта'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    image = models.ImageField(
        upload_to='recepies/images/',
        null=True,
        default=None
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientsRecipes')
    tags = models.ManyToManyField(
        Tags,
        through='TagsRecipes')
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
    

class TagsRecipes(models.Model):
    tag = models.ForeignKey(
        Tags,
        on_delete=models.CASCADE,
        verbose_name='Тэг')
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')


class IngredientsRecipes(models.Model):
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент')
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество'
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
        User, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following')

    class Meta:
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
        Recipes,
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


class Favorites(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    recipe = models.ForeignKey(
        Recipes,
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

