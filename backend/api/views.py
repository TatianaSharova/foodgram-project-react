from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (IsAuthenticated,
                                        AllowAny)
from recipes.models import Recipe, Tag, Ingredient, Cart, Favorite, Follow, IngredientRecipe, User

from .serializers import (RecipeListSerializer, RecipeCreateSerializer,
                          TagSerializer, IngredientSerializer,
                          FavoriteSerializer, CartSerializer, FollowSerializer)

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


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)

                
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

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        '''Добавляем или удаляем рецепт из избранного.'''
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            if Favorite.objects.filter(author=user,
                                       recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен в избранное.'},
                                status=HTTPStatus.BAD_REQUEST)
            serializer = FavoriteSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data,
                                status=HTTPStatus.CREATED)
            return Response(serializer.errors,
                            status=HTTPStatus.BAD_REQUEST)
        if request.method == 'DELETE':
            if not Favorite.objects.filter(author=user,
                                       recipe=recipe).exists():
                return Response({'errors': 'Объект не найден'},
                            status=HTTPStatus.NOT_FOUND)
            Favorite.objects.get(recipe=recipe).delete()
            return Response('Рецепт удалён из избранного.',
                            status=HTTPStatus.NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, **kwargs):
        '''Добавляем или удаляем рецепт из списка покупок.'''
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            if Cart.objects.filter(author=user,
                                           recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=HTTPStatus.BAD_REQUEST)
            serializer = CartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipe=recipe)
                return Response(serializer.data,
                                status=HTTPStatus.CREATED)
            return Response(serializer.errors,
                            status=HTTPStatus.BAD_REQUEST)
        if request.method == 'DELETE':
            if not Cart.objects.filter(author=user,
                                       recipe=recipe).exists():
                return Response({'errors': 'Рецепт не найден.'},
                                status=HTTPStatus.NOT_FOUND)
            Cart.objects.get(recipe=recipe).delete()
            return Response('Рецепт удалён из списка покупок.',
                        status=HTTPStatus.NO_CONTENT)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        '''Скачиваем список покупок для выбранных рецептов.'''
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
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
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

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
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        '''Оформление подписки на автора или отписка от него.'''
        following = get_object_or_404(User, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
            serializer = FollowSerializer(
                data=request.data,
                context={'request': request, 'following': following})
            if serializer.is_valid(raise_exception=True):
                serializer.save(following=following, user=user)
                return Response({'Вы подписались на автора рецептов.': serializer.data},
                                status=HTTPStatus.CREATED)
            return Response(serializer.errors,
                            status=HTTPStatus.BAD_REQUEST)
        if request.method == 'DELETE':
            if Follow.objects.filter(following=following, user=user).exists():
                Follow.objects.get(following=following).delete()
                return Response('Вы отписались от автора.',
                                status=HTTPStatus.NO_CONTENT)
            return Response({'errors': 'Объект не найден'},
                            status=HTTPStatus.NOT_FOUND)
