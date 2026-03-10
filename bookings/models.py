from django.db import models
from django.contrib.auth.models import User
from hotels.models import RoomType


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('cancelled', 'Đã hủy'),
        ('completed', 'Hoàn thành'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField(verbose_name="Ngày nhận phòng")
    check_out = models.DateField(verbose_name="Ngày trả phòng")
    guests = models.IntegerField(default=1, verbose_name="Số khách")
    special_requests = models.TextField(blank=True, verbose_name="Yêu cầu đặc biệt")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Đặt phòng"
        verbose_name_plural = "Đặt phòng"
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} {self.user.username} — {self.room_type}"

    def nights(self):
        return (self.check_out - self.check_in).days

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out:
            nights = (self.check_out - self.check_in).days
            self.total_price = self.room_type.price_per_night * max(nights, 1)
        super().save(*args, **kwargs)