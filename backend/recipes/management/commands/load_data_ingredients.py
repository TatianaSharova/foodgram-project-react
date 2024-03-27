from csv import DictReader

from django.core.management import BaseCommand

# Import the model
from recipes.models import Ingredients

ALREDY_LOADED_ERROR_MESSAGE = """
If you need to reload the child data from the CSV file,
first delete the db.sqlite3 file to destroy the database.
Then, run `python manage.py migrate` for a new empty
database with tables"""


class Command(BaseCommand):
    """Кастомная команда для загрузки данных из CSV-файлов в БД"""
    help = "Loads data from category.csv"

    def handle(self, *args, **options):
        if Ingredients.objects.exists():
            print('category data already loaded...exiting.')
            print(ALREDY_LOADED_ERROR_MESSAGE)
            return
        print("Loading category data")
        for row in DictReader(open('./ingredients.csv', encoding='utf-8')):
            ingredient = Ingredients(
                name=row['name'],
                measure=row['measure'])
            ingredient.save()