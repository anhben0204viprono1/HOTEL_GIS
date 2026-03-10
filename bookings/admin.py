from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'room_type', 'check_in', 'check_out', 'status', 'total_price']
    list_filter = ['status', 'check_in']
    search_fields = ['user__username', 'room_type__hotel__name']
    list_editable = ['status']