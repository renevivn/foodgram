import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Exists, OuterRef, Value
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)
from rest_framework import serializers
from users.models import Subscription

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор Тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, author):
        """Проверяет, подписан ли текущий пользователем на автора."""
        request = self.context.get('request')
        return bool(request) and author.subscribers.filter(
            user_id=request.user.pk,
        ).exists()


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента в рецепте (для чтения)."""

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name',)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта (для чтения)."""

    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True,
    )
    tags = TagSerializer(many=True, read_only=True,)
    text = serializers.CharField(read_only=True,)

    is_favorited = serializers.BooleanField(read_only=True,)
    is_in_shopping_cart = serializers.BooleanField(read_only=True,)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента в рецепте (для записи)."""

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class Base64ImageField(serializers.ImageField):
    """Поле изображения с поддержкой Base64."""

    def to_internal_value(self, image_data):
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            image_data = ContentFile(
                base64.b64decode(imgstr),
                name=f'temp.{ext}'
            )

        return super().to_internal_value(image_data)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта (для записи)."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False,
    )
    ingredients = IngredientWriteSerializer(many=True, allow_empty=False)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def add_ingredients(self, recipe, ingredients):
        """
        Общий метод для create и update.

        Создает связи рецепта с ингредиентами.
        """

        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        self.add_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if tags is not None:
            instance.tags.clear()
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipe_ingredients.clear()
            self.add_ingredients(instance, ingredients)

        return instance

    def to_representation(self, instance):
        """
        Сериализует рецепт через RecipeReadSerializer.

        Добавляет аннотации is_favorited и is_in_shopping_cart на основе
        текущего авторизованного пользователя.
        """

        request = self.context.get('request')
        user = request.user
        annotated = Recipe.objects.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
            ) if user.is_authenticated else Value(False),
            is_in_shopping_cart=Exists(
                ShoppingList.objects.filter(user=user, recipe=OuterRef('pk'))
            ) if user.is_authenticated else Value(False),
        ).get(pk=instance.pk)
        return RecipeReadSerializer(annotated, context=self.context).data

    def validate(self, data):
        """Проверяет наличие обязательных полей при обновлении рецепта."""

        if self.context['request'].method not in ('PATCH', 'PUT'):
            return data
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле.'}
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                {'tags': 'Обязательное поле.'}
            )
        return data

    # Не вынесено в общий метод:
    # validate_ingredients работает со списком объектов,
    # validate_tags — со списком хэшируемых значений.

    def validate_ingredients(self, value):
        """Проверяет, что список ингредиентов без повторов."""
        ids = [item['id'] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return value

    def validate_tags(self, value):
        """Проверяет, что список тегов без повторов."""
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта с минимальным набором полей."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с рецептами (для подписок)."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipe.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields: tuple = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def validate_recipes_limit(self, limit):
        """Проверяет, что recipes_limit является целым числом."""
        try:
            return int(limit)
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                {'recipes_limit': 'Должно быть целым числом.'}
            )

    def get_recipes(self, obj):
        """Возвращает список рецептов пользователя с учетом лимита."""

        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipe.all()

        if limit:
            recipes = recipes[:self.validate_recipes_limit(limit)]

        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context
        ).data


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для установки аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class UserRecipeBaseSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранного и списка покупок."""

    class Meta:
        fields = ('user', 'recipe',)


class FavoriteSerializer(UserRecipeBaseSerializer):
    """Сериализатор для избранного."""

    class Meta(UserRecipeBaseSerializer.Meta):
        model = Favorite


class ShoppingListSerializer(UserRecipeBaseSerializer):
    """Сериализатор для списка покупок."""

    class Meta(UserRecipeBaseSerializer.Meta):
        model = ShoppingList


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author',)

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError('Нельзя подписаться на себя.')
        return data
