import re

from rest_framework.validators import ValidationError


def validate_color(value):
    '''Валидация слага цвета.'''
    match = re.search(r'^[-a-zA-Z0-9_]+$', value)
    if not match:
        raise ValidationError(
            'Некорректный слаг!'
        )
