import base64
from rest_framework import exceptions, serializers
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator
import webcolors
from django.core.files.base import ContentFile

from recipes.models import Recipe, Tag, Ingredient, Follow, Cart, Favorite, IngredientRecipe, User


class UserInfoSerializer(UserSerializer):
    '''Serializer для просмотра пользователя.'''

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        '''Проверка на подписку.'''
        user_id = self.context.get("request").user.id
        return Follow.objects.filter(
            user=user_id, following=obj.id
        ).exists()


class UserCreationSerializer(UserCreateSerializer):
    '''Serializer для создания пользователя.'''

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class TagsField(serializers.SlugRelatedField):

    def to_representation(self, value):
        request = self.context.get('request')
        context = {'request': request}
        serializer = TagSerializer(value, context=context)
        return serializer.data


class FollowListSerializer(serializers.Serializer):

    class Meta:
        model = Follow


class FollowSerializer(serializers.ModelSerializer):
    '''Serializer для оформления подписки.'''
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='following.recipes.count')

    class Meta:
        model = Follow
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following')
            )
        ]

    def validate_following(self, data):
        if Follow.objects.filter(
                fillowing=data.get('following'),
                user=self.context['request'].user).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
        )
        if self.context['request'].user != data.get('following'):
            return data
        raise serializers.ValidationError(
            'Нельзя подписаться на себя!'
        )

    def get_recipes(self, obj):
        '''Получаем рецепты автора.'''
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        '''Количество рецептов автора.'''
        return Recipe.objects.filter(author=obj.id).count()
    
    def get_is_subscribed(self, obj):
        '''Проверка на подписку.'''
        user_id = self.context.get("request").user.id
        return Follow.objects.filter(
            user=user_id, following=obj.id
        ).exists()


class IngredientSerializer(serializers.ModelSerializer):
    '''Serializer для ингредиентов.'''

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    '''Serializer для простмотра ингредиентов в рецепте.'''
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')



class CreateRecipeIngredientsSerializer(serializers.ModelSerializer):
    '''Serializer для создания ингредиентов в рецепте. '''
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')



class RecipeListSerializer(serializers.ModelSerializer):
    '''Serializer для просмотра рецептов.'''
    author = UserInfoSerializer()
    tags = TagSerializer(
        many=True,
        read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ("pub_date",)

    def get_is_favorited(self, obj):
        '''Находится ли рецепт в избранном.'''
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Favorite.objects.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        '''Находится ли рецепт в корзине покупок.'''
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Cart.objects.filter(recipe=obj).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''Serializer для создания, обновления и удаления рецепта.'''
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault())
    ingredients = CreateRecipeIngredientsSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time', 'author')

    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Нужно добавить хотя бы 1 ингредиент!'
                )
        ingredients_list = []
        for item in value:
            ingredient = get_object_or_404(Ingredient, name=item['id'])
            if ingredient in ingredients_list:
                raise exceptions.ValidationError(
                    'Ингредиенты не должны повторяться!'
                )
            ingredients_list.append(ingredient)
        return value

    def validate_tags(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Нужно выбрать хотя бы 1 тэг!'
            )
        tags_list = []
        for tag in value:
            if tag in tags_list:
                raise exceptions.ValidationError(
                    'Тэги не должны повторяться!'
                )
            tags_list.append(tag)
        return value

    def to_representation(self, instance):
        ingredients = super().to_representation(instance)
        ingredients['ingredients'] = IngredientRecipeSerializer(
            instance.recipe_ingredients.all(), many=True).data
        return ingredients

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = get_object_or_404(
                Ingredient, pk=ingredient.get('id').id
            )
            IngredientRecipe.objects.create(
                recipe=recipe, ingredient=ingredient, amount=amount
            )
        return recipe


    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        if tags:
            instance.tags.set(tags)

        ingredients = validated_data.pop('ingredients')
        if ingredients:
            instance.ingredients.clear()

            for ingredient in ingredients:
                amount = ingredient.get('amount')
                ingredient = get_object_or_404(
                    Ingredient, pk=ingredient.get('id').id
                )

                IngredientRecipe.objects.update_or_create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=amount,
                )
        return super().update(instance, validated_data)



class RecipeShortSerializer(serializers.ModelSerializer):
    '''Serializer для вывода рецептов в подписках.'''
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image',)


class FavoriteSerializer(serializers.ModelSerializer):
    '''Serializer для избранных рецептов.'''
    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True)
    name = serializers.ReadOnlyField(
        source='recipe.name',
        read_only=True)
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True)
    coocking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'coocking_time')


class CartSerializer(serializers.ModelSerializer):
    '''Serializer для добавления рецепта в список покупок.'''
    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True)
    name = serializers.ReadOnlyField(
        source='recipe.name',
        read_only=True)
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True)
    coocking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'name', 'image', 'coocking_time')