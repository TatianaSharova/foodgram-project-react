from django.http import HttpResponse


def generate_shopping_list(file_name, ingredients):
    shopping_list = []
    for item in ingredients:
        name = item['ingredient__name']
        measurement_unit = item['ingredient__measurement_unit']
        amount = item['ingredient_total']
        shopping_list.append(f'{name} - {amount} {measurement_unit}')
    content = '\n'.join(shopping_list)
    content_type = 'text/plain,charset=utf8'
    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename={file_name}'
    return response
