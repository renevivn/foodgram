import json

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из JSON файла.'

    def handle(self, *args, **kwargs):
        with open(
            settings.BASE_DIR / 'data' / 'ingredients.json',
            encoding='utf-8'
        ) as f:
            data = json.load(f)
        for item in data:
            Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
        self.stdout.write('Ингредиенты загружены!')
