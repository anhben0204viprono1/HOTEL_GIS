from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('book/<int:room_type_id>/', views.create_booking, name='create'),
    path('<int:pk>/',                views.booking_detail, name='detail'),
    path('<int:pk>/cancel/',         views.cancel_booking, name='cancel'),
    path('<int:pk>/payment/',        views.booking_create_payment, name='create_payment'),
    path('payments/<int:payment_id>/', views.payment_page, name='payment_page'),
    path('payments/<int:payment_id>/paid/', views.payment_mark_paid, name='payment_mark_paid'),
    path('payments/<int:payment_id>/momo/return/', views.momo_return, name='momo_return'),
    path('payments/momo/ipn/', views.momo_ipn, name='momo_ipn'),
]
