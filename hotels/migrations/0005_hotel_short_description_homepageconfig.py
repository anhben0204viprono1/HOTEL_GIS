from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotels', '0004_hotel_amenities_roomtype_price_per_hour'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotel',
            name='short_description',
            field=models.CharField(
                blank=True, max_length=300,
                verbose_name='Mô tả ngắn',
                help_text='Hiển thị trong card danh sách và hero. Tối đa 300 ký tự.'
            ),
        ),
        migrations.CreateModel(
            name='HomepageConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('hero_tagline',       models.CharField(default='Hệ thống GIS · Tích hợp bản đồ · Dịch vụ phòng', max_length=150, verbose_name='Tagline (chữ nhỏ trên hero)')),
                ('hero_title',         models.CharField(default='Khám Phá Khách Sạn Tốt Nhất Việt Nam', max_length=200, verbose_name='Tiêu đề hero lớn')),
                ('hero_subtitle',      models.CharField(blank=True, default='', max_length=300, verbose_name='Phụ đề hero (dòng nhỏ dưới tiêu đề)')),
                ('hero_image_url',     models.CharField(default='https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=1800&q=80', max_length=500, verbose_name='URL ảnh nền hero')),
                ('hero_cta_text',      models.CharField(default='Khám phá ngay', max_length=80, verbose_name='Nút CTA hero (text)')),
                ('showcase_title',     models.CharField(default='Trải Nghiệm Đẳng Cấp', max_length=150, verbose_name='Tiêu đề section tiện nghi')),
                ('showcase_subtitle',  models.CharField(blank=True, default='Hàng trăm tiện ích được tích hợp sẵn trong từng phòng khách sạn.', max_length=300, verbose_name='Mô tả section tiện nghi')),
                ('promo_title',        models.CharField(blank=True, default='', max_length=150, verbose_name='Tiêu đề promo section')),
                ('promo_body',         models.TextField(blank=True, default='', verbose_name='Nội dung promo (HTML hoặc text)')),
                ('site_announcement',  models.TextField(blank=True, default='', verbose_name='Thông báo nổi (hiển thị đầu trang nếu có)')),
                ('updated_at',         models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Cấu hình trang chủ', 'verbose_name_plural': 'Cấu hình trang chủ'},
        ),
    ]
