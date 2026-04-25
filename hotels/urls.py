from django.urls import path
from . import views, views_services

app_name = 'hotels'

urlpatterns = [
    # ── Danh sách & chi tiết khách sạn ──────────────────────────────────────
    path('', views.hotel_list, name='list'),
    path('hotels/<str:slug>/', views.hotel_detail, name='detail'),

    # ── Chi tiết loại phòng + lịch trống/bận ────────────────────────────────
    path('hotels/room-types/<int:pk>/', views.room_type_detail, name='room_type_detail'),

    # ── GeoJSON API ──────────────────────────────────────────────────────────
    path('api/hotels/geojson/', views.hotels_geojson_api, name='geojson_api'),

    # ── Room Service Portal (khách đang ở gọi dịch vụ) ──────────────────────
    path(
        'hotels/<str:hotel_slug>/room/<str:room_number>/services/',
        views_services.room_service_portal,
        name='room_service_portal',
    ),
    path(
        'hotels/<str:hotel_slug>/room/<str:room_number>/services/request/',
        views_services.submit_service_request,
        name='submit_service_request',
    ),
    path(
        'hotels/service-request/<int:request_id>/status/',
        views_services.check_request_status,
        name='check_request_status',
    ),
    path(
        'hotels/service-request/<int:request_id>/update/',
        views_services.staff_update_request,
        name='staff_update_request',
    ),
]
