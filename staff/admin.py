from django.contrib import admin
from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'hotel', 'role', 'phone', 'is_active', 'hired_at']
    list_filter   = ['hotel', 'role', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'hotel__name']
    autocomplete_fields = ['user', 'hotel']

    def full_name(self, obj):
        return obj.full_name()
    full_name.short_description = 'Họ tên'
