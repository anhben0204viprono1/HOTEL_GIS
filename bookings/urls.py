from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # ── Đặt phòng ─────────────────────────────────────────────────────────
    path('book/<int:room_type_id>/',      views.create_booking,  name='create'),
    path('<int:pk>/',                      views.booking_detail,  name='detail'),
    path('<int:pk>/cancel/',               views.cancel_booking,  name='cancel'),

    # ── Thanh toán ────────────────────────────────────────────────────────
    path('<int:pk>/payment/',              views.payment_page,    name='payment'),
    path('<int:pk>/payment/result/',       views.payment_result,  name='payment_result'),
    path('<int:pk>/payment/counter/',      views.pay_at_counter,  name='pay_counter'),

    # ── MoMo ──────────────────────────────────────────────────────────────
    path('<int:pk>/payment/momo/',         views.initiate_momo,   name='momo_init'),
    path('<int:pk>/payment/momo/return/',  views.momo_return,     name='momo_return'),
    path('<int:pk>/payment/momo/ipn/',     views.momo_ipn,        name='momo_ipn'),
]