from django.urls import path
from .views import search_hotels

urlpatterns = [
    path("search/", search_hotels),
]
