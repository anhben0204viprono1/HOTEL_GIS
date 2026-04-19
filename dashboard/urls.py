from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # ── Home ──────────────────────────────────────────────────────
    path('',                                    views.dashboard_home,        name='home'),

    # ── Hotels ────────────────────────────────────────────────────
    path('hotels/',                             views.hotel_list,            name='hotel_list'),
    path('hotels/create/',                      views.hotel_create,          name='hotel_create'),
    path('hotels/<int:pk>/edit/',               views.hotel_edit,            name='hotel_edit'),
    path('hotels/<int:pk>/delete/',             views.hotel_delete,          name='hotel_delete'),
    path('hotels/<int:pk>/toggle/',             views.hotel_toggle,          name='hotel_toggle'),

    # ── RoomTypes (loại phòng) — gắn theo hotel ───────────────────
    path('hotels/<int:hotel_pk>/room-types/',            views.roomtype_list,    name='roomtype_list'),
    path('hotels/<int:hotel_pk>/room-types/create/',     views.roomtype_create,  name='roomtype_create'),
    path('hotels/<int:hotel_pk>/room-types/<int:pk>/edit/',   views.roomtype_edit,   name='roomtype_edit'),
    path('hotels/<int:hotel_pk>/room-types/<int:pk>/delete/', views.roomtype_delete, name='roomtype_delete'),

    # ── Rooms (phòng thực tế) — gắn theo hotel ────────────────────
    path('hotels/<int:hotel_pk>/rooms/',                 views.room_by_hotel,   name='room_by_hotel'),
    path('hotels/<int:hotel_pk>/rooms/create/',          views.room_create,     name='room_create'),
    path('hotels/<int:hotel_pk>/rooms/bulk/',            views.room_bulk_create,name='room_bulk'),
    path('hotels/<int:hotel_pk>/rooms/<int:pk>/edit/',   views.room_edit,       name='room_edit'),
    path('hotels/<int:hotel_pk>/rooms/<int:pk>/delete/', views.room_delete,     name='room_delete'),

    # ── Bookings ──────────────────────────────────────────────────
    path('bookings/',                           views.booking_list,          name='booking_list'),
    path('bookings/<int:pk>/',                  views.booking_detail,        name='booking_detail'),
    path('bookings/<int:pk>/status/',           views.booking_update_status, name='booking_status'),

    # ── Rooms (tổng hợp tất cả) ───────────────────────────────────
    path('rooms/',                              views.room_list,             name='room_list'),
    path('rooms/<int:pk>/status/',              views.room_update_status,    name='room_status'),

    # ── Users ─────────────────────────────────────────────────────
    path('users/',                              views.user_list,             name='user_list'),
    path('users/<int:pk>/toggle/',              views.user_toggle,           name='user_toggle'),
    path('users/<int:pk>/permissions/',         views.user_permissions,      name='user_permissions'),

    # ── API ───────────────────────────────────────────────────────
    path('api/stats/',                          views.api_stats,             name='api_stats'),
]
