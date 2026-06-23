from django.contrib import admin
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)

admin.site.empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Панель администратора для модели Tag."""

    list_display = ('name', 'slug',)
    search_fields = ('name', 'slug',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Панель администратора для модели Ingredient."""

    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Панель администратора для модели Recipe."""

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj):
        return obj.favorite_set.count()

    list_display = ('name', 'author',)
    search_fields = ('name', 'author__username',)
    list_filter = ('tags',)
    readonly_fields = ('get_favorite_count',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Панель администратора для модели RecipeIngredient."""

    list_display = ('recipe', 'ingredient', 'amount',)
    search_fields = ('recipe__name', 'ingredient__name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Панель администратора для модели Favorite."""

    list_display = ('user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    """Панель администратора для модели ShoppingList."""

    list_display = ('user', 'recipe',)
    search_fields = ('user__username', 'recipe__name',)
