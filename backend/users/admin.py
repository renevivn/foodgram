from django.contrib import admin
from users.models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Панель администратора для модели CustomUser."""

    list_display = ('username', 'email', 'first_name', 'last_name',)
    search_fields = ('username', 'email',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Панель администратора для модели Subscription."""

    list_display = ('user', 'author',)
    search_fields = (
        'user__username',
        'user__email',
        'author__username',
        'author__email',
    )
