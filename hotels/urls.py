from django.urls import path
from . import views

app_name = 'hotels'

urlpatterns = [
    path('', views.hotel_list, name='list'),
    path('hotels/<str:slug>/', views.hotel_detail, name='detail'),
    path('api/hotels/geojson/', views.hotels_geojson_api, name='geojson_api'),
]
