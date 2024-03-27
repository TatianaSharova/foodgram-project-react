from rest_framework import filters, mixins, viewsets
from rest_framework.pagination import PageNumberPagination
from .serializers import (FollowSerializer, TagSerializer)
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        AllowAny)
from recipes.models import Recipe
from .serializers import ShowRecipeSerializers
from rest_framework.decorators import action
from io import BytesIO
from django.http import FileResponse


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = ShowRecipeSerializers

    @action(detail=False,methods=["GET"])
    def download_shopping_cart(self, request):
        data = ...
        a = BytesIO(data.encode('utf8'))
        return FileResponse(a, as_attachment=True)
    
    @action(detail=True,methods='POST')
    def shopping_cart(self, request, pk=None):
        ...
    
    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk=None):
        ...

                


class CreateListViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    pass


class FollowViewSet(CreateListViewSet):
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('following__username',)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Получаем queryset авторов, на кого подписан user."""
        user = self.request.user
        return user.follower.all()
