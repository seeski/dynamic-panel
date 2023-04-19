from django.http import HttpResponse, HttpResponseNotFound
from . import services
import time

# чтобы не засерать файлик с вьюхами
# все вспомогательные функции вынесены в файлик services.py

# вьюха на сбор категорий
async def update_categories(request):
    await services.update_categories_file()
    return HttpResponse('good')


# вьюха на сбор даты по отдельной категории
async def scrape_category(request, category: str):
    start = time.time()
    products = await services.scrape_category(category=category)
    products_list = services.products_to_list(products)

    if products_list:
        services.create_category_json(category_name=category, products=products_list)
        print(time.time() - start)
        return HttpResponse('good')

    else:
        print(time.time() - start)
        return HttpResponseNotFound('something went wrong')