# Foodgram

# **Описание**

Foodgram — сервис для публикации рецептов. Пользователи могут регистрироваться, публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на авторов. Сервис позволяет формировать список покупок и скачивать его в виде текстового файла.

Проект развёрнут в Docker-контейнерах.

# **Использованные технологии**

- [Python 3.12](https://docs.python.org/3.12/) — язык программирования для backend-части проекта
- [Django 5.1](https://docs.djangoproject.com/) — backend-фреймворк
- [Django REST Framework](https://www.django-rest-framework.org/) — инструменты для создания REST API
- [Djoser](https://djoser.readthedocs.io/en/latest/) — библиотека для работы с пользователями и токен-аутентификацией
- [PostgreSQL](https://www.postgresql.org/docs/) — реляционная база данных
- [React](https://react.dev/) — библиотека для разработки frontend-интерфейса
- [Docker](https://docs.docker.com/) — платформа для контейнеризации приложения
- [Docker Compose](https://docs.docker.com/compose/) — инструмент для запуска многоконтейнерного приложения
- [Nginx](https://nginx.org/en/docs/) — веб-сервер
- [Gunicorn](https://gunicorn.org/) — WSGI-сервер для запуска Django
- [Git](https://git-scm.com/docs) — система контроля версий

# **Установка**

- Клонировать репозиторий и перейти в него:

```git clone https://github.com/renevivn/foodgram.git```
```cd foodgram```

- Создать файл `.env` в папке `infra/` и заполнить переменные окружения:

```env
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

- Запустить проект в контейнерах:

```docker compose -f infra/docker-compose.yml up -d --build```

- Создать суперпользователя:

```docker compose exec backend python manage.py createsuperuser```

- Загрузить ингредиенты в базу данных:
```docker compose -f infra/docker-compose.yml exec backend python manage.py load_ingredients```

# **Примеры запросов**

- Регистрация пользователя:

POST /api/users/

```json
{
  "username": "new_user",
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Ренев",
  "password": "strong_password"
}
```

- Получение списка рецептов:

GET /api/recipes/

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Борщ",
      "image": "http://localhost/media/recipe_images/borscht.jpg",
      "cooking_time": 60,
      "tags": [{"id": 1, "name": "Обед", "slug": "lunch"}],
      "author": {"id": 1, "username": "user1"},
      "is_favorited": false,
      "is_in_shopping_cart": false
    }
  ]
}
```

- Добавить рецепт в избранное:

POST /api/recipes/{id}/favorite/

- Скачать список покупок:

GET /api/recipes/download_shopping_cart/

# Адрес проекта

http://81.26.190.31/

# **Автор**

Иван Ренев
GitHub: https://github.com/renevivn