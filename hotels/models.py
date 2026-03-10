from django.db import models


class HotelCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Danh mục")

    class Meta:
        verbose_name = "Danh mục khách sạn"
        verbose_name_plural = "Danh mục khách sạn"

    def __str__(self):
        return self.name


class Hotel(models.Model):
    STAR_CHOICES = [(i, f"{i} sao") for i in range(1, 6)]

    name = models.CharField(max_length=200, verbose_name="Tên khách sạn")
    slug = models.SlugField(unique=True, allow_unicode=True)
    category = models.ForeignKey(HotelCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Danh mục")
    description = models.TextField(verbose_name="Mô tả")
    address = models.CharField(max_length=300, verbose_name="Địa chỉ")
    city = models.CharField(max_length=100, verbose_name="Thành phố", default="Hồ Chí Minh")
    latitude = models.FloatField(verbose_name="Vĩ độ")
    longitude = models.FloatField(verbose_name="Kinh độ")
    stars = models.IntegerField(choices=STAR_CHOICES, default=3, verbose_name="Số sao")
    price_per_night = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Giá / đêm (VNĐ)")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    image = models.ImageField(upload_to='hotels/', blank=True, null=True, verbose_name="Ảnh chính")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Khách sạn"
        verbose_name_plural = "Khách sạn"
        ordering = ['-stars', 'name']

    def __str__(self):
        return self.name

    def star_range(self):
        return range(self.stars)

    def get_amenity_list(self):
        return self.amenities.all()


class RoomType(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='room_types', verbose_name="Khách sạn")
    name = models.CharField(max_length=100, verbose_name="Tên phòng")
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Giá / đêm")
    capacity = models.IntegerField(default=2, verbose_name="Sức chứa (người)")
    total_rooms = models.IntegerField(default=10, verbose_name="Tổng số phòng")
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)

    class Meta:
        verbose_name = "Loại phòng"
        verbose_name_plural = "Loại phòng"

    def __str__(self):
        return f"{self.hotel.name} — {self.name}"


class Amenity(models.Model):
    ICON_CHOICES = [
        ('wifi', '📶 WiFi'), ('pool', '🏊 Hồ bơi'), ('gym', '🏋️ Gym'),
        ('spa', '💆 Spa'), ('restaurant', '🍽️ Nhà hàng'), ('parking', '🚗 Bãi xe'),
        ('bar', '🍸 Bar'), ('beach', '🏖️ Bãi biển'), ('airport', '✈️ Đưa đón sân bay'),
        ('laundry', '👕 Giặt ủi'), ('ac', '❄️ Điều hòa'), ('breakfast', '🍳 Bữa sáng'),
    ]
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='amenities')
    icon = models.CharField(max_length=20, choices=ICON_CHOICES)

    def __str__(self):
        return dict(self.ICON_CHOICES).get(self.icon, self.icon)

    class Meta:
        verbose_name = "Tiện nghi"
        verbose_name_plural = "Tiện nghi"


class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hotels/gallery/')
    caption = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Ảnh khách sạn"
        verbose_name_plural = "Ảnh khách sạn"

    def __str__(self):
        return f"Ảnh {self.hotel.name}"