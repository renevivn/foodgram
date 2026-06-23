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
        UserViewSet.as_view({'put': 'avatar', 'delete': 'avatar'}),
        name='user-avatar'
    ),
    path(
        'users/subscriptions/',
        UserViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),
    path(
        'users/<int:pk>/subscribe/',
        UserViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
        name='user-subscribe'
    ),
]

v1_urlpatterns = [
    path('', include(v1_router.urls)),
    path('', include(urlpatterns_users)),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include('djoser.urls')),
]

urlpatterns = [
    path('api/', include(v1_urlpatterns)),
]
