from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # ── Đặt phòng ─────────────────────────────────────────────────────────
    path('book/<int:room_type_id>/',          views.create_booking,          name='create'),
    path('book-hourly/<int:room_type_id>/',   views.create_hourly_booking,   name='create_hourly'),
    path('<int:pk>/',                          views.booking_detail,          name='detail'),
    path('<int:pk>/cancel/',                   views.cancel_booking,          name='cancel'),
    path('my/',                                views.my_bookings,             name='my_bookings'),

    # ── Thanh toán ────────────────────────────────────────────────────────
    path('<int:pk>/payment/',              views.payment_page,    name='payment'),
    path('<int:pk>/payment/confirm/', views.confirm_payment, name='confirm_payment'),
    path('<int:pk>/payment/result/',       views.payment_result,  name='payment_result'),

    # ── Review sau checkout ───────────────────────────────────────────────
    path('<int:pk>/review/',               views.create_review,   name='review'),

    # ── Tiện nghi sử dụng khi đang ở ─────────────────────────────────────
    path('<int:pk>/amenities/',            views.amenity_usage,   name='amenity_usage'),

    # ── Trang chi tiết booking cho user (service request) ─────────────────
    path('<int:pk>/detail/',               views.booking_detail_user,    name='detail_user'),
    path('<int:booking_pk>/service-request/', views.submit_service_request, name='service_request'),
]
