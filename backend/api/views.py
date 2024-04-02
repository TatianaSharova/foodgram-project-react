from rest_framework import mixins, viewsets
from rest_framework import exceptions
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (IsAuthenticated,
                                        AllowAny)
from recipes.models import Recipe, Tag, Ingredient, Cart, Favorite, Follow, IngredientRecipe, User

from .serializers import (RecipeListSerializer, RecipeCreateSerializer,
                          TagSerializer, IngredientSerializer,
                          FavoriteSerializer, CartSerializer, FollowSerializer,
                          UserInfoSerializer)

from .pagination import LimitPagination

from .filters import RecipeFilter


from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAuthorOrAdminOrReadOnly
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from http import HTTPStatus
from django.db.models import Sum
from django.http import HttpResponse
from djoser.views import UserViewSet


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
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
        """
        Получить / Добавить / Удалить  рецепт
        из избранного у текущего пользоватля.
        """
        try:
            recipe = Recipe.objects.get(id=self.kwargs.get('pk'))
        except Recipe.DoesNotExist:
            return Response({'errors': 'Объект не найден'},
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
            return Response({'errors': 'Объект не найден'},
                            status=HTTPStatus.BAD_REQUEST)
        Favorite.objects.filter(author=user,recipe=recipe).delete()
        return Response('Рецепт успешно удалён из избранного.',
                        status=HTTPStatus.NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        """
        Получить / Добавить / Удалить  рецепт
        из списка покупок у текущего пользоватля.
        """
        try:
            recipe = Recipe.objects.get(id=self.kwargs.get('pk'))
        except Recipe.DoesNotExist:
            return Response({'errors': 'Объект не найден'},
                            status=HTTPStatus.BAD_REQUEST)
        user = self.request.user
        if request.method == 'POST':
            if Cart.objects.filter(author=user,recipe=recipe).exists():
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
        Cart.objects.filter(author=user,recipe=recipe).delete()
        return Response('Рецепт успешно удалён из списка покупок.',
                        status=HTTPStatus.NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        '''Скачиваем список покупок для выбранных рецептов.'''
        ingredients = IngredientRecipe.objects.filter(
            recipe__cart__author=self.request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(ingredient_total=Sum('amount'))
        file_name = 'shopping_list.txt'
        shopping_list = []
        for item in ingredients:
            name = item['ingredient__name']
            measurement_unit = item['ingredient__measurement_unit']
            amount = item['ingredient_total']
            shopping_list.append(f'{name} - {amount} {measurement_unit}')
        content = '\n'.join(shopping_list)
        content_type = 'text/plain,charset=utf8'
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        return response


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
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
                return Response(
                    f'Вы отписались.',
                    status=HTTPStatus.NO_CONTENT
                )
            return Response(
                'Такой подписки не существует',
                status=HTTPStatus.BAD_REQUEST
            )
