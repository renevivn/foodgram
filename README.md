[Русская версия](README.ru.md)

# Foodgram

## Description

Foodgram is a recipe-sharing service. Users can sign up, publish recipes, add other users' recipes to favorites and follow authors. The service builds a shopping list from selected recipes and lets users download it as a text file.

The project runs in Docker containers.

## Tech stack

- [Python 3.12](https://docs.python.org/3.12/)
- [Django 5.1](https://docs.djangoproject.com/) — web framework
- [Django REST Framework](https://www.django-rest-framework.org/) — REST API
- [Djoser](https://djoser.readthedocs.io/en/latest/) — user management and token authentication
- [PostgreSQL](https://www.postgresql.org/docs/) — database
- [React](https://react.dev/) — frontend
- [Docker](https://docs.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) — containerization
- [Nginx](https://nginx.org/en/docs/) — reverse proxy, static and media files
- [Gunicorn](https://gunicorn.org/) — WSGI server
- [GitHub Actions](https://docs.github.com/en/actions) — CI/CD

## Getting started

Clone the repository and go to the project folder:

```bash
git clone https://github.com/renevivn/foodgram.git
cd foodgram
```

Create a `.env` file in the `infra/` folder (see `.env.example`):

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

Start the containers (migrations and static collection run automatically when the backend starts):

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Create a superuser and load the ingredients:

```bash
docker compose -f infra/docker-compose.yml exec backend python manage.py createsuperuser
docker compose -f infra/docker-compose.yml exec backend python manage.py load_ingredients
```

The app will be available at http://localhost/, the API documentation at http://localhost/api/docs/redoc.html.

## API examples

Register a user:

`POST /api/users/`

```json
{
  "username": "new_user",
  "email": "user@example.com",
  "first_name": "Ivan",
  "last_name": "Renev",
  "password": "strong_password"
}
```

Get the list of recipes:

`GET /api/recipes/`

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Borscht",
      "image": "http://localhost/media/recipe_images/borscht.jpg",
      "cooking_time": 60,
      "tags": [{"id": 1, "name": "Lunch", "slug": "lunch"}],
      "author": {"id": 1, "username": "user1"},
      "is_favorited": false,
      "is_in_shopping_cart": false
    }
  ]
}
```

Add a recipe to favorites:

`POST /api/recipes/{id}/favorite/`

Download the shopping list:

`GET /api/recipes/download_shopping_cart/`

## Deployment

The project was deployed to a training server via the GitHub Actions pipeline (tests → Docker Hub → SSH deploy); that server is no longer available. The app can be run locally as described above.

## Author

Ivan Renev — [github.com/renevivn](https://github.com/renevivn)
