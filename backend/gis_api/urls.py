from django.urls import path
from .views import search_accommodation, home

urlpatterns = [
    path("", home),
    path("search/", search_accommodation),
]
