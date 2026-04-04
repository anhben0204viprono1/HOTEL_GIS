"""
bookings/models.py
Thiết kế theo schema PostgreSQL:
  Booking → Payment
  Booking → Review
"""
from django.db import models
from django.contrib.auth.models import User
from hotels.models import Room, Hotel
from django.core.exceptions import ValidationError
from django.utils import timezone


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
                check=models.Q(check_out__gt=models.F('check_in')),
                name='chk_checkout_after_checkin'
            )
        ]

    def __str__(self):
        return f'#{self.id} — {self.user.get_full_name() or self.user.username} | {self.room}'

    def nights(self):
        """Số đêm ở."""
        return (self.check_out - self.check_in).days

    def clean(self):
        errors = {}

        if self.user_id and not self.user.is_active:
            errors['user'] = 'Tài khoản đang bị khóa.'

        today = timezone.localdate()
        if self.check_in and self.check_in < today:
            errors['check_in'] = 'Ngày nhận phòng không được trong quá khứ.'

        if self.check_in and self.check_out:
            if self.check_out <= self.check_in:
                errors['check_out'] = 'Ngày trả phòng phải sau ngày nhận phòng.'
            if (self.check_out - self.check_in).days > 30:
                errors['check_out'] = 'Không thể đặt phòng quá 30 đêm liên tiếp.'

        if self.room_id:
            if self.room.status == 'maintenance':
                errors['room'] = 'Phòng đang bảo trì, không thể đặt.'

            if self.num_guests and self.room.room_type_id:
                max_occ = self.room.room_type.max_occupancy
                if self.num_guests > max_occ:
                    errors['num_guests'] = f'Loại phòng này chỉ chứa tối đa {max_occ} khách.'

        # Không cho phép trùng lịch cho cùng 1 room với booking đang active
        if self.room_id and self.check_in and self.check_out:
            active_statuses = ['pending', 'confirmed', 'checked_in']
            overlap_qs = (
                Booking.objects
                .filter(
                    room_id=self.room_id,
                    status__in=active_statuses,
                    check_in__lt=self.check_out,
                    check_out__gt=self.check_in,
                )
            )
            if self.pk:
                overlap_qs = overlap_qs.exclude(pk=self.pk)
            if overlap_qs.exists():
                errors['room'] = 'Phòng đã được đặt trong khoảng ngày bạn chọn.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Cho phép skip validate khi seed/fixture
        if not kwargs.pop('skip_clean', False):
            self.full_clean()

        previous_status = None
        if self.pk:
            previous_status = (
                Booking.objects.filter(pk=self.pk)
                .values_list('status', flat=True)
                .first()
            )

        # Tự tính tổng tiền = số đêm × giá phòng
        if self.check_in and self.check_out and self.room_id:
            n = (self.check_out - self.check_in).days
            self.total_price = self.room.room_type.price_per_night * max(n, 1)
        super().save(*args, **kwargs)

        if previous_status != self.status:
            self._sync_room_status(previous_status, self.status)

    def _sync_room_status(self, previous_status, new_status):
        """
        Đồng bộ Room.status theo vòng đời booking.
        - checked_in  -> occupied
        - checked_out/cancelled (từ checked_in) -> available (nếu không bảo trì và không còn ai đang ở)
        """
        if not self.room_id:
            return

        room = self.room

        if new_status == 'checked_in':
            if room.status != 'maintenance' and room.status != 'occupied':
                room.status = 'occupied'
                room.save(update_fields=['status', 'updated_at'])
            return

        if previous_status == 'checked_in' and new_status in ('checked_out', 'cancelled'):
            if room.status == 'maintenance':
                return
            has_other_checked_in = (
                Booking.objects
                .filter(room_id=room.id, status='checked_in')
                .exclude(pk=self.pk)
                .exists()
            )
            if not has_other_checked_in and room.status != 'available':
                room.status = 'available'
                room.save(update_fields=['status', 'updated_at'])

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
    reference        = models.CharField(
        max_length=64, blank=True,
        verbose_name='Mã tham chiếu'
    )
    qr_payload       = models.TextField(
        blank=True,
        verbose_name='Nội dung QR (payload/link)'
    )
    qr_url           = models.URLField(
        max_length=500, blank=True,
        verbose_name='URL ảnh QR'
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

    QR_METHODS = {'bank_transfer', 'e_wallet', 'momo', 'vnpay', 'zalopay'}

    def wants_qr(self):
        return self.method in self.QR_METHODS and self.status == 'pending'

    def set_qr(self, payload: str):
        """
        Tạo QR URL từ payload mà không phụ thuộc thư viện ngoài.
        Ảnh QR được render qua dịch vụ tạo QR miễn phí.
        """
        from urllib.parse import quote_plus
        self.qr_payload = payload or ''
        if self.qr_payload:
            data = quote_plus(self.qr_payload)
            self.qr_url = f'https://api.qrserver.com/v1/create-qr-code/?size=240x240&data={data}'
        else:
            self.qr_url = ''


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
