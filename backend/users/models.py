from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from users.constants import (EMAIL_MAX_LENGTH, FIRST_NAME_MAX_LENGTH,
                             LAST_NAME_MAX_LENGTH, USERNAME_MAX_LENGTH,
                             USERNAME_REGEX)
from users.validators import validate_username_not_me


class User(AbstractUser):
    """Кастомная модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    email = models.EmailField(
        'Адрес электронной почты',
        max_length=EMAIL_MAX_LENGTH,
        unique=True
    )
    username = models.CharField(
        'Уникальный юзернейм',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=USERNAME_REGEX,
                message=(
                    'Введите корректное имя пользователя. '
                    'Допустимы латинские буквы, цифры и символы @ . + - _.'
                )
            ),
            validate_username_not_me,
        ],
    )
    first_name = models.CharField('Имя', max_length=FIRST_NAME_MAX_LENGTH,)
    last_name = models.CharField('Фамилия', max_length=LAST_NAME_MAX_LENGTH,)
    avatar = models.ImageField(
        'Ссылка на аватар',
        null=True,
        blank=True,
        upload_to='avatar_image',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        default_related_name = 'user'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписка пользователя на автора."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscriptions',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='subscribers',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                name='unique_user_author_subscription',
                fields=('author', 'user'),
            ),
            models.CheckConstraint(
                name='prevent_self_subscription',
                condition=~models.Q(user=models.F('author')),
            )
        ]

    def clean(self):
        """Запрещает подписку на самого себя."""
        super().clean()
        if self.user == self.author:
            raise ValidationError(
                'Нельзя подписаться на самого себя!'
            )

    def __str__(self):
        return (
            f'Пользователь {self.user} подписался на публикации {self.author}.'
        )
