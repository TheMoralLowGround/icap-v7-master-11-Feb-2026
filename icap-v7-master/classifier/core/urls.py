from django.urls import path

from core import views

urlpatterns = [
    path(
        "title_classification/", views.title_classification, name="title_classification"
    ),
    path(
        "manual_classification/",
        views.manual_classification,
        name="manual_classification",
    ),
    path("ignore_dense_pages/", views.ignore_dense_pages, name="ignore_dense_pages"),
    path("get_custom_category/", views.get_custom_category, name="get_custom_category"),
    path("create_custom_category/", views.create_custom_category, name="create_custom_category"),
]
