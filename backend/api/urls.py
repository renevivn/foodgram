from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
from django.urls import include, path
from rest_framework.routers import SimpleRouter

v1_router = SimpleRouter()

v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns_users = [
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    path(
        'users/me/avatar/',
        UserViewSet.as_view({'put': 'avatar', 'delete': 'avatar_delete'}),
        name='user-avatar'
    ),
    path(
        'users/subscriptions/',
        UserViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),
    path(
        'users/<int:pk>/subscribe/',
        UserViewSet.as_view(
            {'post': 'subscribe', 'delete': 'subscribe_delete'}
        ),
        name='user-subscribe'
    ),
    path(
        'recipes/<int:pk>/favorite/',
        RecipeViewSet.as_view(
            {'post': 'favorite_add', 'delete': 'favorite_delete'}
        ),
        name='recipe-favorite'
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        RecipeViewSet.as_view(
            {'post': 'shopping_cart_add', 'delete': 'shopping_cart_delete'}
        ),
        name='recipe-shopping-cart'
    ),
]

v1_urlpatterns = [
    path('', include(urlpatterns_users)),
    path('', include(v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]

urlpatterns = [
    path('api/', include(v1_urlpatterns)),
]
