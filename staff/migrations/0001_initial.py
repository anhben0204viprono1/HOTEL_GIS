"""
staff/migrations/0001_initial.py
"""
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hotels', '0001_initial'),
        ('bookings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('manager','👔 Quản lý khách sạn'),('receptionist','🛎 Lễ tân'),('housekeeping','🧹 Dọn phòng'),('maintenance','🔧 Kỹ thuật')], default='receptionist', max_length=20, verbose_name='Chức vụ')),
                ('phone', models.CharField(blank=True, max_length=20, verbose_name='Số điện thoại')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='staff/avatars/', verbose_name='Ảnh đại diện')),
                ('is_active', models.BooleanField(default=True, verbose_name='Đang hoạt động')),
                ('hired_at', models.DateField(blank=True, null=True, verbose_name='Ngày vào làm')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('hotel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_members', to='hotels.hotel', verbose_name='Khách sạn phụ trách')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='staff_profile', to=settings.AUTH_USER_MODEL, verbose_name='Tài khoản')),
            ],
            options={'verbose_name': 'Nhân viên', 'verbose_name_plural': 'Nhân viên', 'ordering': ['hotel', 'user__last_name']},
        ),
        migrations.CreateModel(
            name='ServiceRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_type', models.CharField(choices=[('room_service','🍽 Room Service'),('housekeeping','🧹 Dọn phòng'),('maintenance','🔧 Sửa chữa / Kỹ thuật'),('amenity','🛎 Yêu cầu tiện ích'),('transport','🚖 Đặt xe / Đưa đón'),('laundry','👕 Giặt ủi'),('checkout_early','🚪 Trả phòng sớm'),('checkin_late','⌛ Nhận phòng muộn'),('other','📝 Khác')], default='other', max_length=20, verbose_name='Loại yêu cầu')),
                ('title', models.CharField(max_length=200, verbose_name='Tiêu đề')),
                ('description', models.TextField(blank=True, verbose_name='Mô tả chi tiết')),
                ('priority', models.CharField(choices=[('low','🟢 Thấp'),('medium','🟡 Trung bình'),('high','🔴 Cao'),('urgent','🚨 Khẩn cấp')], default='medium', max_length=10, verbose_name='Mức độ ưu tiên')),
                ('status', models.CharField(choices=[('pending','⏳ Chờ xử lý'),('in_progress','🔄 Đang xử lý'),('resolved','✅ Đã giải quyết'),('cancelled','❌ Đã hủy')], default='pending', max_length=15, verbose_name='Trạng thái')),
                ('staff_note', models.TextField(blank=True, verbose_name='Ghi chú xử lý')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='Thời điểm giải quyết')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('hotel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_requests', to='hotels.hotel', verbose_name='Khách sạn')),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='service_requests', to='bookings.booking', verbose_name='Đặt phòng liên quan')),
                ('room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='service_requests', to='hotels.room', verbose_name='Phòng')),
                ('guest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='service_requests', to=settings.AUTH_USER_MODEL, verbose_name='Khách hàng')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_requests', to='staff.staffprofile', verbose_name='Nhân viên phụ trách')),
            ],
            options={'verbose_name': 'Yêu cầu dịch vụ', 'verbose_name_plural': 'Yêu cầu dịch vụ', 'ordering': ['-created_at']},
        ),
        migrations.AddIndex(
            model_name='servicerequest',
            index=models.Index(fields=['hotel', 'status'], name='idx_staff_sreq_hotel_status'),
        ),
        migrations.AddIndex(
            model_name='servicerequest',
            index=models.Index(fields=['status'], name='idx_staff_sreq_status'),
        ),
        migrations.AddIndex(
            model_name='servicerequest',
            index=models.Index(fields=['priority'], name='idx_staff_sreq_priority'),
        ),
    ]
