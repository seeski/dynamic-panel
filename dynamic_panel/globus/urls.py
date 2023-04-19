from . import views
from django.urls import path


urlpatterns =  [
    path('update_categories', views.update_categories, name='update_categories'),# вьюха на обновление файлика с категориями
    path('<category>', views.scrape_category, name='category'), # на сбор даты по каждой категории
]