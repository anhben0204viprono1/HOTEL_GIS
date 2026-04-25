"""
staff/models.py

Models cho hệ thống nhân viên khách sạn:
  - StaffProfile: liên kết User ↔ Hotel (1 nhân viên quản lý 1 khách sạn)
  - ServiceRequest: yêu cầu dịch vụ / tiện ích từ khách hàng
"""
from django.db import models
from django.contrib.auth.models import User
from hotels.models import Hotel, Room
from bookings.models import Booking


# ─── 1. StaffProfile ──────────────────────────────────────────────────────────

class StaffProfile(models.Model):
    """
    Hồ sơ nhân viên — mở rộng User mặc định của Django.
    Mỗi nhân viên được gán quản lý đúng 1 khách sạn.
    """
    ROLE_CHOICES = [
        ('manager',     '👔 Quản lý khách sạn'),
        ('receptionist','🛎 Lễ tân'),
        ('housekeeping','🧹 Dọn phòng'),
        ('maintenance', '🔧 Kỹ thuật'),
    ]

    user       = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='staff_profile',
        verbose_name='Tài khoản'
    )
    hotel      = models.ForeignKey(
        Hotel, on_delete=models.CASCADE,
        related_name='staff_members',
        verbose_name='Khách sạn phụ trách'
    )
    role       = models.CharField(
        max_length=20, choices=ROLE_CHOICES,
        default='receptionist', verbose_name='Chức vụ'
    )
    phone      = models.CharField(max_length=20, blank=True, verbose_name='Số điện thoại')
    avatar     = models.ImageField(
        upload_to='staff/avatars/', blank=True, null=True,
        verbose_name='Ảnh đại diện'
    )
    is_active  = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    hired_at   = models.DateField(null=True, blank=True, verbose_name='Ngày vào làm')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Nhân viên'
        verbose_name_plural = 'Nhân viên'
        ordering            = ['hotel', 'user__last_name']

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} — {self.hotel.name}'

    def full_name(self):
        return self.user.get_full_name() or self.user.username
