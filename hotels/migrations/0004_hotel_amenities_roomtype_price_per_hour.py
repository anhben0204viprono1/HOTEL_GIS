from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotels', '0003_hotelservice_servicerequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='roomtype',
            name='price_per_hour',
            field=models.DecimalField(
                blank=True, decimal_places=2, help_text='Để trống sẽ tự tính = giá đêm / 24',
                max_digits=12, null=True, verbose_name='Giá / giờ (VNĐ)'
            ),
        ),
        migrations.AddField(
            model_name='hotel',
            name='amenities',
            field=models.ManyToManyField(
                blank=True, related_name='hotels',
                to='hotels.amenity', verbose_name='Tiện nghi khách sạn'
            ),
        ),
    ]
