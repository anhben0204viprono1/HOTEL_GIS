from django.urls import path
from .views import search_hotels

urlpatterns = [
    path("hotels/search/", search_hotels),
]
