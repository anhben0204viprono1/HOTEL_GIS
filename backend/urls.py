from django.contrib import admin
from django.urls import path, include
from gis_api import views as gis_views

urlpatterns = [
    # Project-level admin booking routes (handled by our app views)
    path("admin/bookings/", gis_views.admin_bookings, name="admin_bookings"),
    path("admin/bookings/<int:booking_id>/", gis_views.booking_detail, name="booking_detail_admin"),
    path("admin/approve-booking/", gis_views.approve_booking, name="approve_booking"),
    path("admin/reject-booking/", gis_views.reject_booking, name="reject_booking"),

    # Django admin site
    path("admin/", admin.site.urls),

    # Application URLs
    path("", include("gis_api.urls")),   # 🔴 BẮT BUỘC
]
