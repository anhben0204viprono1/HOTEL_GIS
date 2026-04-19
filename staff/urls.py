"""
staff/urls.py
"""
from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Home
    path('',                                        views.staff_home,                    name='home'),

    # Rooms
    path('rooms/',                                  views.staff_rooms,                   name='rooms'),
    path('rooms/<int:pk>/status/',                  views.staff_room_update_status,      name='room_status'),

    # Bookings
    path('bookings/',                               views.staff_bookings,                name='bookings'),
    path('bookings/<int:pk>/',                      views.staff_booking_detail,          name='booking_detail'),

    # Service Requests
    path('requests/',                               views.staff_service_requests,        name='service_requests'),
    path('requests/create/',                        views.staff_service_request_create,  name='service_request_create'),
    path('requests/<int:pk>/update/',               views.staff_service_request_update,  name='service_request_update'),

    # API
    path('api/stats/',                              views.staff_api_stats,               name='api_stats'),
]
