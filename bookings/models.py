"""
bookings/models.py
Thiết kế theo schema PostgreSQL:
  Booking → Payment
  Booking → Review
"""
from django.db import models
from django.contrib.auth.models import User
from hotels.models import Room, Hotel


# ─── 1. Booking ───────────────────────────────────────────────────────────────

class Booking(models.Model):
    """
    Đặt phòng — tương ứng bảng Booking trong SQL schema.
    Đặt theo Room thực tế (không phải RoomType).
    """
    STATUS_CHOICES = [
        ('pending',      '⏳ Chờ xác nhận'),
        ('confirmed',    '✅ Đã xác nhận'),
        ('checked_in',   '🏨 Đang ở'),
        ('checked_out',  '🚪 Đã trả phòng'),
        ('cancelled',    '❌ Đã hủy'),
    ]

    user            = models.ForeignKey(
        User, on_delete=models.RESTRICT,
        related_name='bookings', verbose_name='Khách hàng'
    )
    room            = models.ForeignKey(
        Room, on_delete=models.RESTRICT,
        related_name='bookings', verbose_name='Phòng'
    )
    check_in        = models.DateField(verbose_name='Ngày nhận phòng')
    check_out       = models.DateField(verbose_name='Ngày trả phòng')
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
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Đặt phòng'
        verbose_name_plural = 'Đặt phòng'
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['user'],             name='idx_booking_customer'),
            models.Index(fields=['room'],             name='idx_booking_room'),
            models.Index(fields=['check_in', 'check_out'], name='idx_booking_dates'),
            models.Index(fields=['status'],           name='idx_booking_status'),
        ]
        constraints = [
            # Tương ứng: CONSTRAINT chk_dates CHECK (check_out > check_in)
            models.CheckConstraint(
                condition=models.Q(check_out__gt=models.F('check_in')),
                name='chk_checkout_after_checkin'
            )
        ]

    def __str__(self):
        return f'#{self.id} — {self.user.get_full_name() or self.user.username} | {self.room}'

    def nights(self):
        """Số đêm ở."""
        return (self.check_out - self.check_in).days

    def save(self, *args, **kwargs):
        # Tự tính tổng tiền = số đêm × giá phòng
        if self.check_in and self.check_out and self.room_id:
            n = (self.check_out - self.check_in).days
            self.total_price = self.room.room_type.price_per_night * max(n, 1)
        super().save(*args, **kwargs)

    def can_cancel(self):
        return self.status in ('pending', 'confirmed')

    def can_review(self):
        return self.status == 'checked_out' and not hasattr(self, 'review')


# ─── 2. Payment ───────────────────────────────────────────────────────────────

class Payment(models.Model):
    """
    Thanh toán — tương ứng bảng Payment trong SQL schema.
    """
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
    amount           = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Số tiền'
    )
    method           = models.CharField(
        max_length=20, choices=METHOD_CHOICES, verbose_name='Phương thức'
    )
    status           = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending', verbose_name='Trạng thái'
    )
    transaction_code = models.CharField(
        max_length=100, blank=True, verbose_name='Mã giao dịch'
    )
    gateway_response = models.TextField(
        blank=True, verbose_name='Phản hồi cổng thanh toán (JSON)'
    )
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
    """
    Đánh giá sau khi trả phòng — tương ứng bảng Review trong SQL schema.
    1 booking chỉ được review 1 lần (OneToOne với Booking).
    """
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