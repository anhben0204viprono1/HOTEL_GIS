from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('book/<int:room_type_id>/', views.create_booking, name='create'),
    path('<int:pk>/',                views.booking_detail, name='detail'),
    path('<int:pk>/cancel/',         views.cancel_booking, name='cancel'),
]