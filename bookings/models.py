"""
bookings/models.py
Booking → Payment → Review
Bổ sung: booking_type (daily/hourly), AmenityUsage
"""
from django.db import models
from django.contrib.auth.models import User
from hotels.models import Room, Hotel
from decimal import Decimal


# ─── 1. Booking ───────────────────────────────────────────────────────────────

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending',      '⏳ Chờ xác nhận'),
        ('confirmed',    '✅ Đã xác nhận'),
        ('checked_in',   '🏨 Đang ở'),
        ('checked_out',  '🚪 Đã trả phòng'),
        ('cancelled',    '❌ Đã hủy'),
    ]
    BOOKING_TYPE_CHOICES = [
        ('daily',  'Theo ngày'),
        ('hourly', 'Theo giờ'),
    ]

    user            = models.ForeignKey(
        User, on_delete=models.RESTRICT,
        related_name='bookings', verbose_name='Khách hàng'
    )
    room            = models.ForeignKey(
        Room, on_delete=models.RESTRICT,
        related_name='bookings', verbose_name='Phòng'
    )

    # ── Loại đặt phòng ──────────────────────────────────────────────────────
    booking_type    = models.CharField(
        max_length=10, choices=BOOKING_TYPE_CHOICES,
        default='daily', verbose_name='Loại đặt phòng'
    )

    # Theo ngày (giữ nguyên)
    check_in        = models.DateField(null=True, blank=True, verbose_name='Ngày nhận phòng')
    check_out       = models.DateField(null=True, blank=True, verbose_name='Ngày trả phòng')

    # Theo giờ
    check_in_dt     = models.DateTimeField(null=True, blank=True, verbose_name='Giờ nhận phòng')
    check_out_dt    = models.DateTimeField(null=True, blank=True, verbose_name='Giờ trả phòng')

    num_guests      = models.SmallIntegerField(default=1, verbose_name='Số khách')
    total_price     = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0, verbose_name='Tổng tiền (VNĐ)'
    )
    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending', verbose_name='Trạng thái'
    )
    note            = models.TextField(blank=True, verbose_name='Yêu cầu đặc biệt')
    cancelled_at    = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm hủy')
    cancel_reason   = models.TextField(blank=True, verbose_name='Lý do hủy')
    requires_prepayment = models.BooleanField(
        default=False, verbose_name='Bắt buộc thanh toán trước'
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Đặt phòng'
        verbose_name_plural = 'Đặt phòng'
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['user'],                  name='idx_booking_customer'),
            models.Index(fields=['room'],                  name='idx_booking_room'),
            models.Index(fields=['check_in', 'check_out'], name='idx_booking_dates'),
            models.Index(fields=['status'],                name='idx_booking_status'),
        ]

    def __str__(self):
        return f'#{self.id} — {self.user.get_full_name() or self.user.username} | {self.room}'

    # ── Helpers ─────────────────────────────────────────────────────────────

    def nights(self):
        """Số đêm (chỉ có ý nghĩa khi booking_type == 'daily')."""
        if self.check_in and self.check_out:
            return (self.check_out - self.check_in).days
        return 0

    def hours(self):
        """Số giờ (chỉ có ý nghĩa khi booking_type == 'hourly')."""
        if self.check_in_dt and self.check_out_dt:
            delta = self.check_out_dt - self.check_in_dt
            return max(round(delta.total_seconds() / 3600, 1), 1)
        return 0

    def is_hourly(self):
        return self.booking_type == 'hourly'

    def checkin_display(self):
        if self.booking_type == 'hourly' and self.check_in_dt:
            return self.check_in_dt
        return self.check_in

    def checkout_display(self):
        if self.booking_type == 'hourly' and self.check_out_dt:
            return self.check_out_dt
        return self.check_out

    def save(self, *args, **kwargs):
        # Tự tính tổng tiền
        if self.room_id:
            rt = self.room.room_type
            if self.booking_type == 'hourly' and self.check_in_dt and self.check_out_dt:
                delta   = self.check_out_dt - self.check_in_dt
                hrs     = max(delta.total_seconds() / 3600, 1)
                if rt.price_per_hour:
                    rate = rt.price_per_hour
                else:
                    rate = (rt.price_per_night / Decimal('24')).quantize(Decimal('1'))
                self.total_price = rate * Decimal(str(round(hrs, 1)))
            elif self.booking_type == 'daily' and self.check_in and self.check_out:
                n = (self.check_out - self.check_in).days
                self.total_price = rt.price_per_night * max(n, 1)
        super().save(*args, **kwargs)

    def can_cancel(self):
        return self.status in ('pending', 'confirmed')

    def can_review(self):
        """
        Chỉ cho đánh giá khi:
        1. Trạng thái = checked_out (đã trả phòng)
        2. Chưa có review nào cho booking này
        """
        if self.status != 'checked_out':
            return False
        try:
            self.review  # raises RelatedObjectDoesNotExist nếu chưa có
            return False  # đã có review rồi
        except Exception:
            return True


# ─── 2. Payment ───────────────────────────────────────────────────────────────

class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash',          '💵 Tiền mặt'),
        ('credit_card',   '💳 Thẻ tín dụng'),
        ('debit_card',    '💳 Thẻ ghi nợ'),
        ('bank_transfer', '🏦 Chuyển khoản'),
        ('e_wallet',      '📱 Ví điện tử'),
        ('momo',          '🟣 MoMo'),
        ('vnpay',         '🔵 VNPay'),
        ('zalopay',       '🔷 ZaloPay'),
    ]
    STATUS_CHOICES = [
        ('pending',   '⏳ Chờ thanh toán'),
        ('paid',      '✅ Đã thanh toán'),
        ('failed',    '❌ Thất bại'),
        ('refunded',  '🔄 Đã hoàn tiền'),
    ]

    booking          = models.ForeignKey(
        Booking, on_delete=models.RESTRICT,
        related_name='payments', verbose_name='Đặt phòng'
    )
    amount           = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Số tiền')
    method           = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name='Phương thức')
    status           = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending', verbose_name='Trạng thái'
    )
    transaction_code = models.CharField(max_length=100, blank=True, verbose_name='Mã giao dịch')
    gateway_response = models.TextField(blank=True, verbose_name='Phản hồi cổng thanh toán (JSON)')
    paid_at          = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm thanh toán')
    refunded_at      = models.DateTimeField(null=True, blank=True, verbose_name='Thời điểm hoàn tiền')
    refund_amount    = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name='Số tiền hoàn'
    )
    note             = models.TextField(blank=True, verbose_name='Ghi chú kế toán')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Thanh toán'
        verbose_name_plural = 'Thanh toán'
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['booking'],          name='idx_payment_booking'),
            models.Index(fields=['status'],           name='idx_payment_status'),
            models.Index(fields=['transaction_code'], name='idx_payment_transaction'),
        ]

    def __str__(self):
        return f'Payment #{self.id} — {self.get_method_display()} — {self.get_status_display()}'


# ─── 3. Review ────────────────────────────────────────────────────────────────

class Review(models.Model):
    booking    = models.OneToOneField(
        Booking, on_delete=models.CASCADE,
        related_name='review', verbose_name='Đặt phòng'
    )
    user       = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='reviews', verbose_name='Khách hàng'
    )
    hotel      = models.ForeignKey(
        Hotel, on_delete=models.CASCADE,
        related_name='reviews', verbose_name='Khách sạn'
    )
    rating     = models.SmallIntegerField(
        choices=[(i, f'{i} sao') for i in range(1, 6)],
        verbose_name='Điểm đánh giá (1-5)'
    )
    comment    = models.TextField(blank=True, verbose_name='Nhận xét')
    is_visible = models.BooleanField(default=True, verbose_name='Hiển thị công khai')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Đánh giá'
        verbose_name_plural = 'Đánh giá'
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['hotel'],  name='idx_review_hotel'),
            models.Index(fields=['rating'], name='idx_review_rating'),
        ]

    def __str__(self):
        return f'Review #{self.id} — {self.hotel.name} — {self.rating}★'


# ─── 4. AmenityUsage — Ghi nhận tiện ích sử dụng khi đang ở ─────────────────

class AmenityUsage(models.Model):
    booking  = models.ForeignKey(
        Booking, on_delete=models.CASCADE,
        related_name='amenity_usages', verbose_name='Đặt phòng'
    )
    amenity  = models.ForeignKey(
        'hotels.Amenity', on_delete=models.CASCADE,
        related_name='usages', verbose_name='Tiện nghi'
    )
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name='Số lượng')
    note     = models.TextField(blank=True, verbose_name='Ghi chú')
    used_at  = models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm sử dụng')

    class Meta:
        verbose_name        = 'Sử dụng tiện nghi'
        verbose_name_plural = 'Sử dụng tiện nghi'
        ordering            = ['-used_at']

    def __str__(self):
        return f'#{self.booking_id} — {self.amenity.name} x{self.quantity}'
