import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import exceptions, serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Cart, Favorite, Follow, Ingredient,
                            IngredientRecipe, Recipe, Tag, User)


class UserInfoSerializer(UserSerializer):
    '''Serializer для просмотра пользователя.'''
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        '''Проверка на подписку.'''
        user_id = self.context.get('request').user.id
        return Follow.objects.filter(
            user=user_id, following=obj.id
        ).exists()


class UserCreationSerializer(UserCreateSerializer):
    '''Serializer для создания пользователя.'''

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
        )


class Base64ImageField(serializers.ImageField):
    '''Кодировка изображения.'''
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    '''Serializer для тэгов.'''

    class Meta:
        model = Tag
        fields = '__all__'


class TagsField(serializers.SlugRelatedField):
    '''Поле для просмотра тэгов.'''

    def to_representation(self, value):
        request = self.context.get('request')
        context = {'request': request}
        serializer = TagSerializer(value, context=context)
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    '''Serializer для ингредиентов.'''

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = '__all__',


class IngredientRecipeSerializer(serializers.ModelSerializer):
    '''Serializer для просмотра ингредиентов в рецепте.'''
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateRecipeIngredientsSerializer(serializers.ModelSerializer):
    '''Serializer для создания ингредиентов в рецепте. '''
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError('Ингредиент не существует.')
        return value


class RecipeListSerializer(serializers.ModelSerializer):
    '''Serializer для просмотра рецептов.'''
    author = UserInfoSerializer()
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_ingredients(self, obj):
        ingredients = IngredientRecipe.objects.filter(recipe=obj)
        serializer = IngredientRecipeSerializer(ingredients, many=True)
        return serializer.data

    def get_is_favorited(self, obj):
        '''Находится ли рецепт в избранном.'''
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Favorite.objects.filter(author=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        '''Находится ли рецепт в корзине покупок.'''
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Cart.objects.filter(author=user, recipe=obj).exists()
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''Serializer для создания, обновления и удаления рецепта.'''
    author = UserInfoSerializer(read_only=True)
    ingredients = CreateRecipeIngredientsSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('author', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate(self, data):
        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise exceptions.ValidationError(
                'Необходимо указать ингредиенты.'
            )
        ingredient_ids = [ingredient.get('id') for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise exceptions.ValidationError(
                'Ингредиенты уже были добавлены в рецепт.'
            )
        tags = data.get('tags', [])
        if not tags:
            raise exceptions.ValidationError(
                'Необходимо указать теги.'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться')
        return data

    def to_representation(self, instance):
        return RecipeListSerializer(
            instance, context={'request': self.context.get('request')}
        ).data

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = get_object_or_404(
                Ingredient, id=ingredient.get('id')
            )
            IngredientRecipe.objects.create(
                recipe=recipe, ingredient=ingredient, amount=amount
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags:
            instance.tags.set(tags)

        ingredients = validated_data.pop('ingredients', None)
        if not ingredients or not tags:
            raise exceptions.ValidationError(
                'Необходимо выбрать тэг и ингредиенты!'
            )
        if ingredients:
            instance.ingredients.clear()

            for ingredient in ingredients:
                amount = ingredient.get('amount')
                ingredient = get_object_or_404(
                    Ingredient, id=ingredient.get('id')
                )

                IngredientRecipe.objects.update_or_create(
                    recipe=instance,
                    ingredient=ingredient,
                    defaults={'amount': amount},
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
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')


class CartSerializer(serializers.ModelSerializer):
    '''Serializer для  списка покупок.'''
    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True)
    name = serializers.ReadOnlyField(
        source='recipe.name',
        read_only=True)
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'name', 'image', 'cooking_time')


class UsersRecipeSerializer(serializers.ModelSerializer):
    '''
    Cериализатор для просмотра рецептов из подписок, избранного и корзины.
    '''
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowReadSerializer(serializers.ModelSerializer):
    '''Сериализатор просмотра подписок текущего пользователя.'''
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        '''Проверка на подписку.'''
        user_id = self.context.get('request').user.id
        return Follow.objects.filter(
            user=user_id, following=obj.id
        ).exists()

    def get_recipes(self, obj):
        '''Получение рецептов автора.'''
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)
            queryset = queryset[:recipes_limit]
        serializer = UsersRecipeSerializer(
            queryset,
            many=True,
            context=self.context
        )
        return serializer.data

    def get_recipes_count(self, obj):
        '''Получение количества рецептов автора.'''
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    '''Serializer создания и удаления подписки.'''

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user', 'following')
        validators = (
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Вы уже подписаны на этого автора. '
            ),
        )

    def validate_following(self, value):
        '''Проверка подписки на самого себя и повторной подписки.'''
        user = self.context['request'].user
        following = value
        if user == following:
            raise exceptions.ValidationError(['Нельзя подписаться на себя.'])
        if Follow.objects.filter(
                following=value,
                user=self.context['request'].user).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        return value

    def to_representation(self, instance):
        '''Определяет сериализатор, используемый для чтения.'''
        return FollowReadSerializer(
            instance.following,
            context={'request':
                     self.context['request']}
        ).data
