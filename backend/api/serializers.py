import base64

from django.core.files.base import ContentFile
from django.db.models import Exists, OuterRef, Value
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)
from rest_framework import serializers
from users.models import CustomUser, Subscription


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
        model = CustomUser
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
        """Проверяет, подписан ли текущий пользователь на автора."""

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=author
        ).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователей."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )


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

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class Base64ImageField(serializers.ImageField):
    """Поле изображения с поддержкой Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта (для записи)."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
    )
    ingredients = IngredientWriteSerializer(many=True, required=True,)
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

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
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
            instance.recipe_ingredients.all().delete()
            self.add_ingredients(instance, ingredients)

        instance.save()
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

        if self.context['request'].method in ('PATCH', 'PUT'):
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
        """Проверяет, что список ингредиентов не пустой и без повторов."""

        if not value:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым.'
            )
        ids = [item['id'] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        return value

    def validate_tags(self, value):
        """Проверяет, что список тегов не пустой и без повторов."""

        if not value:
            raise serializers.ValidationError(
                'Список тегов не может быть пустым.'
            )
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
    recipes_count = serializers.SerializerMethodField()

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

    def get_recipes(self, obj):
        """Возвращает список рецептов пользователя с учетом лимита."""

        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipe.all()

        if limit:
            recipes = recipes[:int(limit)]

        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов пользователя."""

        return obj.recipe.count()


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для установки аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)
