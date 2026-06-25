from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from recipes.constants import (INGREDIENT_NAME_MAX_LENGTH,
                               MEASUREMENT_UNIT_MAX_LENGTH, MIN_COOKING_TIME,
                               MIN_INGREDIENT_AMOUNT, RECIPE_NAME_MAX_LENGTH,
                               TAG_NAME_MAX_LENGTH, TAG_SLUG_MAX_LENGTH)


User = get_user_model()


class Tag(models.Model):
    """Тег."""

    name = models.CharField(
        'Название',
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
    )
    slug = models.SlugField(
        'Слаг',
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField('Название', max_length=INGREDIENT_NAME_MAX_LENGTH,)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                name='unique_ingredient',
                fields=('name', 'measurement_unit'),
            ),
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=RECIPE_NAME_MAX_LENGTH,)
    image = models.ImageField('Картинка', upload_to='recipe_images',)
    text = models.TextField('Описание',)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги',)
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(
            MIN_COOKING_TIME,
            message=(
                f'Время приготовления не может быть меньше '
                f'{MIN_COOKING_TIME} мин.'
            )
        ),
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipe'

    def __str__(self):
        return f'Рецепт {self.name}'


class RecipeIngredient(models.Model):
    """
    Промежуточная модель для связи рецепта с ингредиентами.

    Хранит количество каждого ингредиента в рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredient_in_recipes',
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(
            MIN_INGREDIENT_AMOUNT,
            message=(
                f'Количество ингредиентов не может быть меньше '
                f'{MIN_INGREDIENT_AMOUNT}.'
            )
        ),
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                name='unique_recipe_ingredient',
                fields=('recipe', 'ingredient'),
            ),
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name}: {self.amount} '
            f'{self.ingredient.measurement_unit}.'
        )


class UserRecipeBaseModel(models.Model):
    """Абстрактная модель для избранного и списка покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return (
            f'Пользователь {self.user} добавил '
            f'Рецепт {self.recipe} в {self._meta.verbose_name}.'
        )


class Favorite(UserRecipeBaseModel):
    """Избранные рецепты пользователя."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                name='unique_favorite_recipe_user',
                fields=('recipe', 'user'),
            ),
        ]


class ShoppingList(UserRecipeBaseModel):
    """Список покупок пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_list',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                name='unique_shoppinglist_recipe_user',
                fields=('recipe', 'user'),
            ),
        ]
