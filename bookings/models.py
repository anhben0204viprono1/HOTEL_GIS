"""
bookings/models.py
Thiết kế theo schema PostgreSQL:
  Booking → Payment
  Booking → Review
"""
import inspect

from django.db import models
from django.contrib.auth.models import User
from hotels.models import Room, Hotel
from hotels.models import Amenity
from django.core.exceptions import ValidationError
from django.utils import timezone


# Django 6.0 đổi tên tham số CheckConstraint từ `check` → `condition`.
_CHECKCONSTRAINT_EXPR_KWARG = (
    "check"
    if "check" in inspect.signature(models.CheckConstraint).parameters
    else "condition"
)


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

    BOOKING_TYPE_CHOICES = [
        ("daily", "🗓 Theo ngày"),
        ("hourly", "🕐 Theo giờ"),
    ]

    user            = models.ForeignKey(
        User, on_delete=models.RESTRICT,
        related_name='bookings', verbose_name='Khách hàng'
    )
    room            = models.ForeignKey(
        Room, on_delete=models.RESTRICT,
        related_name='bookings', verbose_name='Phòng'
    )
    booking_type    = models.CharField(
        max_length=10,
        choices=BOOKING_TYPE_CHOICES,
        default="daily",
        verbose_name="Loại đặt phòng",
    )
    # Daily booking
    check_in        = models.DateField(null=True, blank=True, verbose_name='Ngày nhận phòng')
    check_out       = models.DateField(null=True, blank=True, verbose_name='Ngày trả phòng')
    # Hourly booking
    check_in_dt     = models.DateTimeField(null=True, blank=True, verbose_name="Giờ nhận phòng")
    check_out_dt    = models.DateTimeField(null=True, blank=True, verbose_name="Giờ trả phòng")
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
            # Daily: check_out > check_in; Hourly: check_out_dt > check_in_dt
            models.CheckConstraint(
                **{
                    _CHECKCONSTRAINT_EXPR_KWARG: models.Q(
                        models.Q(
                            booking_type="daily",
                            check_in__isnull=False,
                            check_out__isnull=False,
                            check_out__gt=models.F("check_in"),
                        )
                        | models.Q(
                            booking_type="hourly",
                            check_in_dt__isnull=False,
                            check_out_dt__isnull=False,
                            check_out_dt__gt=models.F("check_in_dt"),
                        )
                    ),
                    "name": "chk_checkout_after_checkin",
                },
            )
        ]

    def __str__(self):
        return f'#{self.id} — {self.user.get_full_name() or self.user.username} | {self.room}'

    def nights(self):
        """Số đêm ở."""
        if self.booking_type != "daily":
            return 0
        if not self.check_in or not self.check_out:
            return 0
        return (self.check_out - self.check_in).days

    def hours(self):
        """Số giờ ở (booking theo giờ)."""
        if self.booking_type != "hourly":
            return 0
        if not self.check_in_dt or not self.check_out_dt:
            return 0
        seconds = (self.check_out_dt - self.check_in_dt).total_seconds()
        if seconds <= 0:
            return 0
        # Làm tròn lên theo giờ
        import math
        return int(math.ceil(seconds / 3600))

    def clean(self):
        errors = {}

        if self.user_id and not self.user.is_active:
            errors['user'] = 'Tài khoản đang bị khóa.'

        today = timezone.localdate()
        now = timezone.now()

        if self.booking_type == "daily":
            if not self.check_in:
                errors["check_in"] = "Vui lòng chọn ngày nhận phòng."
            if not self.check_out:
                errors["check_out"] = "Vui lòng chọn ngày trả phòng."

            if self.check_in and self.check_in < today:
                errors['check_in'] = 'Ngày nhận phòng không được trong quá khứ.'

            if self.check_in and self.check_out:
                if self.check_out <= self.check_in:
                    errors['check_out'] = 'Ngày trả phòng phải sau ngày nhận phòng.'
                if (self.check_out - self.check_in).days > 30:
                    errors['check_out'] = 'Không thể đặt phòng quá 30 đêm liên tiếp.'

        elif self.booking_type == "hourly":
            if not self.check_in_dt:
                errors["check_in_dt"] = "Vui lòng chọn giờ nhận phòng."
            if not self.check_out_dt:
                errors["check_out_dt"] = "Vui lòng chọn giờ trả phòng."

            if self.check_in_dt and self.check_in_dt < now:
                errors["check_in_dt"] = "Giờ nhận phòng không được trong quá khứ."

            if self.check_in_dt and self.check_out_dt:
                if self.check_out_dt <= self.check_in_dt:
                    errors["check_out_dt"] = "Giờ trả phòng phải sau giờ nhận phòng."
                # Giới hạn 48h để tránh booking theo giờ quá dài
                if (self.check_out_dt - self.check_in_dt).total_seconds() > 48 * 3600:
                    errors["check_out_dt"] = "Không thể đặt theo giờ quá 48 giờ."

        if self.room_id:
            if self.room.status == 'maintenance':
                errors['room'] = 'Phòng đang bảo trì, không thể đặt.'

            if self.num_guests and self.room.room_type_id:
                max_occ = self.room.room_type.max_occupancy
                if self.num_guests > max_occ:
                    errors['num_guests'] = f'Loại phòng này chỉ chứa tối đa {max_occ} khách.'

        # Không cho phép trùng lịch cho cùng 1 room với booking đang active
        active_statuses = ['pending', 'confirmed', 'checked_in']
        if self.room_id:
            overlap_qs = Booking.objects.filter(room_id=self.room_id, status__in=active_statuses)
            if self.pk:
                overlap_qs = overlap_qs.exclude(pk=self.pk)

            if self.booking_type == "daily" and self.check_in and self.check_out:
                # Xung đột với booking daily khác
                daily_conflict = overlap_qs.filter(
                    booking_type="daily",
                    check_in__lt=self.check_out,
                    check_out__gt=self.check_in,
                )

                # Xung đột với booking hourly trong khoảng ngày
                from datetime import datetime, time as dt_time
                start_dt = timezone.make_aware(datetime.combine(self.check_in, dt_time.min))
                end_dt = timezone.make_aware(datetime.combine(self.check_out, dt_time.min))
                hourly_conflict = overlap_qs.filter(
                    booking_type="hourly",
                    check_in_dt__lt=end_dt,
                    check_out_dt__gt=start_dt,
                )

                if daily_conflict.exists() or hourly_conflict.exists():
                    errors["room"] = "Phòng đã được đặt trong khoảng thời gian bạn chọn."

            if self.booking_type == "hourly" and self.check_in_dt and self.check_out_dt:
                # Xung đột với booking hourly khác
                hourly_conflict = overlap_qs.filter(
                    booking_type="hourly",
                    check_in_dt__lt=self.check_out_dt,
                    check_out_dt__gt=self.check_in_dt,
                )

                # Xung đột với booking daily (coi daily block theo ngày)
                from datetime import timedelta
                start_date = timezone.localtime(self.check_in_dt).date()
                end_date = timezone.localtime(self.check_out_dt).date()
                end_exclusive = end_date
                from datetime import time as dt_time
                if timezone.localtime(self.check_out_dt).time() != dt_time(0, 0):
                    end_exclusive = end_date + timedelta(days=1)

                daily_conflict = overlap_qs.filter(
                    booking_type="daily",
                    check_in__lt=end_exclusive,
                    check_out__gt=start_date,
                )

                if hourly_conflict.exists() or daily_conflict.exists():
                    errors["room"] = "Phòng đã được đặt trong khoảng thời gian bạn chọn."

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

        # Tự tính tổng tiền theo loại booking
        if self.room_id:
            rt = self.room.room_type
            if self.booking_type == "daily" and self.check_in and self.check_out:
                n = (self.check_out - self.check_in).days
                self.total_price = rt.price_per_night * max(n, 1)
            if self.booking_type == "hourly" and self.check_in_dt and self.check_out_dt:
                from decimal import Decimal
                hours = max(self.hours(), 1)
                price_per_hour = rt.price_per_hour
                if price_per_hour is None:
                    price_per_hour = (rt.price_per_night / Decimal("24"))
                self.total_price = price_per_hour * Decimal(hours)
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


# ─── 4. Amenity usage ────────────────────────────────────────────────────────

class AmenityUsage(models.Model):
    """
    Ghi nhận khách đang ở sử dụng tiện ích (tiện ích khách sạn hoặc tiện ích phòng).
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="amenity_usages",
        verbose_name="Đặt phòng",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="amenity_usages",
        verbose_name="Khách hàng",
    )
    amenity = models.ForeignKey(
        Amenity,
        on_delete=models.RESTRICT,
        related_name="usages",
        verbose_name="Tiện ích",
    )
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name="Số lượng/lượt")
    note = models.TextField(blank=True, verbose_name="Ghi chú")
    used_at = models.DateTimeField(default=timezone.now, verbose_name="Thời điểm sử dụng")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sử dụng tiện ích"
        verbose_name_plural = "Sử dụng tiện ích"
        ordering = ["-used_at"]
        indexes = [
            models.Index(fields=["booking"], name="idx_amenity_usage_booking"),
            models.Index(fields=["user"], name="idx_amenity_usage_user"),
            models.Index(fields=["amenity"], name="idx_amenity_usage_amenity"),
        ]

    def __str__(self):
        return f"AmenityUsage #{self.id} — booking #{self.booking_id} — {self.amenity.name}"

    def clean(self):
        errors = {}
        if self.booking_id and self.user_id and self.booking.user_id != self.user_id:
            errors["user"] = "User không khớp với booking."
        if self.booking_id and self.booking.status != "checked_in":
            errors["booking"] = "Chỉ được ghi nhận tiện ích khi booking đang ở (checked_in)."
        if errors:
            raise ValidationError(errors)
