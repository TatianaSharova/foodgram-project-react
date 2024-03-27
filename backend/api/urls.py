from django.urls import include, path
from rest_framework.routers import DefaultRouter as Router
from users.views import UserViewset

from api.views import RecipeViewSet

router_v1 = Router()
router_v1.register(r'users', UserViewset, basename='users')
router_v1.register(r'tags', TagViewSet, basename='tag')
router_v1.register(r'recipes', RecipeViewSet, basename='recipe')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredient')


urlpatterns = [
    path("", include(router_v1.urls)),
    path(r'^auth/', include('djoser.urls')),
]