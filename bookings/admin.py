from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Booking, Payment, Review


class PaymentInline(admin.TabularInline):
    model  = Payment
    extra  = 0
    fields = ['amount', 'method', 'status', 'transaction_code', 'paid_at']
    readonly_fields = ['paid_at']

class ReviewInline(admin.StackedInline):
    model  = Review
    extra  = 0
    fields = ['rating', 'comment', 'is_visible']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ['id', 'user', 'room_detail', 'check_in', 'check_out', 'nights_display', 'total_price', 'status_display','status']
    list_filter   = ['status', 'check_in', 'room__hotel__city']
    search_fields = ['user__username', 'user__first_name', 'room__hotel__name', 'room__room_number']
    list_editable = ['status']
    readonly_fields = ['total_price', 'created_at', 'updated_at']
    inlines = [PaymentInline, ReviewInline]

    fieldsets = (
        ('👤 Khách hàng & Phòng', {
            'fields': ('user', 'room', 'num_guests')
        }),
        ('📅 Thời gian', {
            'fields': ('check_in', 'check_out')
        }),
        ('💰 Thanh toán', {
            'fields': ('total_price', 'status')
        }),
        ('📝 Ghi chú', {
            'fields': ('note', 'cancel_reason', 'cancelled_at')
        }),
        ('🕐 Hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    STATUS_COLORS = {
        'pending':     '#d97706',
        'confirmed':   '#2563eb',
        'checked_in':  '#15803d',
        'checked_out': '#6b7280',
        'cancelled':   '#dc2626',
    }

    @admin.display(description='Phòng')
    def room_detail(self, obj):
        return format_html(
            '<span style="font-size:12px;"><b>{}</b><br><small style="color:#6b7280;">{}</small></span>',
            obj.room, obj.room.room_type.name
        )

    @admin.display(description='Số đêm')
    def nights_display(self, obj):
        return format_html('<b>{}</b> đêm', obj.nights())

    @admin.display(description='Trạng thái')
    def status_display(self, obj):
        color = self.STATUS_COLORS.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['id', 'booking', 'amount', 'method_display', 'status_display', 'transaction_code', 'paid_at']
    list_filter   = ['status', 'method']
    search_fields = ['transaction_code', 'booking__id', 'booking__user__username']
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Phương thức')
    def method_display(self, obj):
        return obj.get_method_display()

    @admin.display(description='Trạng thái')
    def status_display(self, obj):
        colors = {'pending':'#d97706','paid':'#15803d','failed':'#dc2626','refunded':'#6b7280'}
        color = colors.get(obj.status, '#6b7280')
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, obj.get_status_display())


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ['id', 'hotel', 'user', 'rating_display', 'comment_short', 'is_visible', 'created_at']
    list_filter   = ['rating', 'is_visible', 'hotel__city']
    search_fields = ['user__username', 'hotel__name', 'comment']
    list_editable = ['is_visible']

    @admin.display(description='Đánh giá')
    def rating_display(self, obj):
        return format_html('<span style="color:#C9A84C;font-weight:700;">{}</span>', '★' * obj.rating)

    @admin.display(description='Nhận xét')
    def comment_short(self, obj):
        return (obj.comment[:60] + '…') if len(obj.comment) > 60 else obj.comment