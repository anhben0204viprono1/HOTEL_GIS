from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_booking_requires_prepayment'),
        ('hotels', '0004_hotel_amenities_roomtype_price_per_hour'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Thêm booking_type
        migrations.AddField(
            model_name='booking',
            name='booking_type',
            field=models.CharField(
                choices=[('daily', 'Theo ngày'), ('hourly', 'Theo giờ')],
                default='daily', max_length=10, verbose_name='Loại đặt phòng'
            ),
        ),
        # Đặt check_in nullable để hỗ trợ hourly
        migrations.AlterField(
            model_name='booking',
            name='check_in',
            field=models.DateField(blank=True, null=True, verbose_name='Ngày nhận phòng'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='check_out',
            field=models.DateField(blank=True, null=True, verbose_name='Ngày trả phòng'),
        ),
        # Thêm datetime fields cho hourly
        migrations.AddField(
            model_name='booking',
            name='check_in_dt',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Giờ nhận phòng'),
        ),
        migrations.AddField(
            model_name='booking',
            name='check_out_dt',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Giờ trả phòng'),
        ),
        # Model AmenityUsage
        migrations.CreateModel(
            name='AmenityUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField(default=1, verbose_name='Số lượng')),
                ('note', models.TextField(blank=True, verbose_name='Ghi chú')),
                ('used_at', models.DateTimeField(auto_now_add=True, verbose_name='Thời điểm sử dụng')),
                ('amenity', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='usages', to='hotels.amenity', verbose_name='Tiện nghi'
                )),
                ('booking', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='amenity_usages', to='bookings.booking', verbose_name='Đặt phòng'
                )),
            ],
            options={
                'verbose_name': 'Sử dụng tiện nghi',
                'verbose_name_plural': 'Sử dụng tiện nghi',
                'ordering': ['-used_at'],
            },
        ),
    ]
