import io

from django.contrib.auth import get_user_model
from django.db.models import Exists, F, OuterRef, Sum, Value
from django.http import FileResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import RecipeFilter
from .mixins import AddMixin, DeleteMixin
from .pagination import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeMinifiedSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, SetAvatarSerializer,
                          ShoppingListSerializer, SubscriptionSerializer,
                          TagSerializer, UserWithRecipesSerializer)


User = get_user_model()


class ReadOnlyNoPaginationViewSet(viewsets.ReadOnlyModelViewSet):
    """Базовый ViewSet только для чтения без пагинации."""

    pagination_class = None


class TagViewSet(ReadOnlyNoPaginationViewSet):
    """ViewSet для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyNoPaginationViewSet):
    """ViewSet для ингредиентов."""

    serializer_class = IngredientSerializer

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if name:
            return Ingredient.objects.filter(name__istartswith=name)
        return Ingredient.objects.all()


class RecipeViewSet(AddMixin, DeleteMixin, viewsets.ModelViewSet):
    """ViewSet для рецептов."""

    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite_add(self, request, pk=None):
        recipe = self.get_object()
        return self.add_instance(
            FavoriteSerializer,
            {'user': request.user.id, 'recipe': recipe.id},
            RecipeMinifiedSerializer(
                recipe,
                context=self.get_serializer_context()
            ).data
        )

    @favorite_add.mapping.delete
    def favorite_delete(self, request, pk=None):
        recipe = self.get_object()
        return self.delete_instance(
            request.user.favorites.filter(recipe=recipe),
            'Запись уже отсутствует.'
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart'
    )
    def shopping_cart_add(self, request, pk=None):
        recipe = self.get_object()
        return self.add_instance(
            ShoppingListSerializer,
            {'user': request.user.id, 'recipe': recipe.id},
            RecipeMinifiedSerializer(
                recipe,
                context=self.get_serializer_context()
            ).data
        )

    @shopping_cart_add.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        recipe = self.get_object()
        return self.delete_instance(
            request.user.shoppinglists.filter(recipe=recipe),
            'Запись уже отсутствует.'
        )

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        recipe_ids = request.user.shoppinglists.values_list(
            'recipe',
            flat=True
        )
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=recipe_ids).values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit')
        ).annotate(
                total_amount=Sum('amount')
        ).order_by('name')

        content = '\n'.join(
            f'{item.get("name", "")} ({item.get("unit", "")}) — '
            f'{item.get("total_amount", 0)}'
            for item in ingredients
        )

        return FileResponse(
            io.BytesIO(content.encode('utf-8')),
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain'
        )

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = request.build_absolute_uri(
            reverse('short_link', args=(recipe.id,))
        )
        return Response({'short-link': short_link})

    def get_serializer_class(self):
        """Возвращает сериализатор для записи (POST/PATCH) или чтения."""
        if self.request.method in {'POST', 'PATCH'}:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_queryset(self):
        """Аннотирует рецепты флагами is_favorited и is_in_shopping_cart."""
        user = self.request.user
        queryset = Recipe.objects.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
            ) if user.is_authenticated else Value(False),
            is_in_shopping_cart=Exists(
                ShoppingList.objects.filter(user=user, recipe=OuterRef('pk'))
            ) if user.is_authenticated else Value(False),
        )
        return queryset


class UserViewSet(DjoserUserViewSet, AddMixin, DeleteMixin):
    """ViewSet для управления пользователями."""

    pagination_class = LimitPagination

    def get_serializer_class(self):
        if self.action in {'subscribe', 'subscriptions'}:
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    @action(detail=False, permission_classes=(IsAuthenticated,), url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=('put',), url_path='me/avatar')
    def avatar(self, request):
        serializer = SetAvatarSerializer(
            request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def avatar_delete(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=('post',), url_path='subscribe')
    def subscribe(self, request, id=None):
        author = self.get_object()
        return self.add_instance(
            SubscriptionSerializer,
            {'user': request.user.id, 'author': author.id},
            self.get_serializer(author).data
        )

    @subscribe.mapping.delete
    def subscribe_delete(self, request, id=None):
        author = self.get_object()
        return self.delete_instance(
            request.user.subscriptions.filter(author=author),
            'Вы не подписаны на этого пользователя.'
        )
