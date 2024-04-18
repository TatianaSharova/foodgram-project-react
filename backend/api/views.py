from http import HTTPStatus

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (CartSerializer, FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeListSerializer, TagSerializer,
                          UserInfoSerializer)
from .utils import generate_shopping_list
from recipes.models import (Cart, Favorite, Follow, Ingredient,
                            IngredientRecipe, Recipe, Tag, User)


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    '''ViewSet для тэгов.'''
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    '''ViewSet для ингредиентов.'''
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    '''
    ViewSet для создания, удаления, редактирования рецептов,
    добавления/удаления их из ибранного,
    добавления/удаления их из списка покупок.
    '''
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    pagination_class = LimitPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeListSerializer
        return RecipeCreateSerializer

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, *args, **kwargs):
        '''
        Добавить или удалить рецепт
        из избранного у текущего пользоватля.
        '''
        try:
            recipe = Recipe.objects.get(id=self.kwargs.get('pk'))
        except Recipe.DoesNotExist:
            return Response({'errors': 'Объект не найден.'},
                            status=HTTPStatus.BAD_REQUEST)
        user = self.request.user
        if request.method == 'POST':
            if Favorite.objects.filter(author=user,
                                       recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=HTTPStatus.BAD_REQUEST)
            serializer = FavoriteSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data,
                                status=HTTPStatus.CREATED)
            return Response(serializer.errors,
                            status=HTTPStatus.BAD_REQUEST)
        if not Favorite.objects.filter(author=user,
                                       recipe=recipe).exists():
            return Response({'errors': 'Объект не найден.'},
                            status=HTTPStatus.BAD_REQUEST)
        Favorite.objects.filter(author=user, recipe=recipe).delete()
        return Response('Рецепт успешно удалён из избранного.',
                        status=HTTPStatus.NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        '''
        Добавляем или удаляем рецепт из списка покупок
        у текущего пользователя.
        '''
        try:
            recipe = Recipe.objects.get(id=self.kwargs.get('pk'))
        except Recipe.DoesNotExist:
            return Response({'errors': 'Объект не найден'},
                            status=HTTPStatus.BAD_REQUEST)
        user = self.request.user
        if request.method == 'POST':
            if Cart.objects.filter(author=user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=HTTPStatus.BAD_REQUEST)
            serializer = CartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data,
                                status=HTTPStatus.CREATED)
            return Response(serializer.errors,
                            status=HTTPStatus.BAD_REQUEST)
        if not Cart.objects.filter(author=user, recipe=recipe).exists():
            return Response({'errors': 'Объект не найден'},
                            status=HTTPStatus.BAD_REQUEST)
        Cart.objects.filter(author=user, recipe=recipe).delete()
        return Response('Рецепт успешно удалён из списка покупок.',
                        status=HTTPStatus.NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        '''Скачиваем список покупок для выбранных рецептов.'''
        ingredients_list = IngredientRecipe.objects.filter(
            recipe__cart__author=self.request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(ingredient_total=Sum('amount'))
        list_name = 'shopping_list.txt'
        return generate_shopping_list(list_name, ingredients_list)


class CustomUserViewSet(UserViewSet):
    '''
    ViewSet для регистрации пользователя, обновления пароля,
    просмотра профиля пользователя по эндпоинту '/me',
    оформления подписок.
    '''
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitPagination

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        '''Получаем профиль пользователя.'''
        user = self.request.user
        serializer = UserInfoSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        '''Подписки данного пользователя.'''
        follows = Follow.objects.filter(user=self.request.user)
        pages = self.paginate_queryset(follows)
        serializer = FollowSerializer(pages,
                                      many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['delete', 'post'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        '''Создание и удаление подписок.'''
        user = request.user
        following = get_object_or_404(User, id=id)
        follow = Follow.objects.filter(user=user, following=following)
        data = {
            'user': user.id,
            'following': following.id,
        }
        if request.method == 'POST':
            serializer = FollowSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTPStatus.CREATED)

        if request.method == 'DELETE':
            if follow.exists():
                follow.delete()
                return Response('Вы отписались.',
                                status=HTTPStatus.NO_CONTENT)
            return Response('Такой подписки не существует.',
                            status=HTTPStatus.BAD_REQUEST)
