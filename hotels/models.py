"""
hotels/models.py
Thiết kế theo schema PostgreSQL:
  Hotel → RoomType → Room → RoomAmenity ← Amenity
  Hotel → HotelImage
"""
from django.db import models
from django.utils.text import slugify
from decimal import Decimal
import math

class HotelCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Hotel(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(HotelCategory, on_delete=models.CASCADE)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def haversine_distance(lat1, lng1, lat2, lng2):
    """Tính khoảng cách (km) giữa 2 tọa độ bằng công thức Haversine."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def unique_slugify_for_model(*, model, value: str, slug_field: str = 'slug', instance_pk=None) -> str:
    """
    Tạo slug unique (append -2, -3...) nếu bị trùng.
    """
    base = slugify(value or '', allow_unicode=True).strip('-')
    if not base:
        base = 'item'

    slug = base
    i = 2
    qs = model._default_manager.all()
    if instance_pk:
        qs = qs.exclude(pk=instance_pk)

    while qs.filter(**{slug_field: slug}).exists():
        slug = f'{base}-{i}'
        i += 1
    return slug


# ─── 1. Amenity ───────────────────────────────────────────────────────────────

class Amenity(models.Model):
    """
    Danh mục tiện ích dùng chung (WiFi, TV, Bồn tắm, ...).
    Tương ứng bảng Amenity trong SQL schema.
    """
    CATEGORY_CHOICES = [
        ('bedroom',       '🛏 Phòng ngủ'),
        ('bathroom',      '🚿 Phòng tắm'),
        ('entertainment', '📺 Giải trí'),
        ('kitchen',       '🍳 Bếp & Ăn uống'),
        ('climate',       '❄️ Nhiệt độ'),
        ('accessibility', '♿ Tiếp cận'),
        ('other',         '📦 Khác'),
    ]

    name        = models.CharField(max_length=100, verbose_name='Tên tiện ích')
    category    = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES,
        default='other', verbose_name='Danh mục'
    )
    icon_url    = models.CharField(max_length=500, blank=True, verbose_name='URL icon')
    description = models.TextField(blank=True, verbose_name='Mô tả')

    class Meta:
        verbose_name         = 'Tiện ích'
        verbose_name_plural  = 'Tiện ích'
        ordering             = ['category', 'name']

    def __str__(self):
        return self.name

    def category_display(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)


# ─── 2. Hotel ─────────────────────────────────────────────────────────────────

class Hotel(models.Model):
    """
    Khách sạn — tương ứng bảng Hotel trong SQL schema.
    Lưu tọa độ GPS để tính khoảng cách Haversine.
    """
    STAR_CHOICES = [(i, f'{i} sao') for i in range(1, 6)]

    name            = models.CharField(max_length=255, verbose_name='Tên khách sạn')
    slug            = models.SlugField(max_length=255, unique=True, allow_unicode=True, blank=True)
    address         = models.CharField(max_length=500, blank=True, verbose_name='Địa chỉ')
    city            = models.CharField(max_length=100, default='Hồ Chí Minh', verbose_name='Thành phố')

    # Tọa độ GPS — khớp với SQL: DECIMAL(10,8) và DECIMAL(11,8)
    latitude        = models.DecimalField(
        max_digits=10, decimal_places=8,
        verbose_name='Vĩ độ (latitude)',
        help_text='Ví dụ: 10.77386000'
    )
    longitude       = models.DecimalField(
        max_digits=11, decimal_places=8,
        verbose_name='Kinh độ (longitude)',
        help_text='Ví dụ: 106.70454900'
    )

    phone           = models.CharField(max_length=20, blank=True, verbose_name='Số điện thoại')
    email           = models.EmailField(blank=True, verbose_name='Email')
    star_rating     = models.SmallIntegerField(
        choices=STAR_CHOICES, default=3, verbose_name='Số sao'
    )
    description     = models.TextField(blank=True, verbose_name='Mô tả')
    thumbnail_url   = models.CharField(max_length=500, blank=True, verbose_name='URL ảnh đại diện')
    image           = models.ImageField(
        upload_to='hotels/', blank=True, null=True,
        verbose_name='Ảnh đại diện (upload)'
    )
    website         = models.URLField(max_length=255, blank=True, verbose_name='Website')

    # Giờ nhận / trả phòng — khớp SQL check_in_time / check_out_time
    check_in_time   = models.TimeField(default='14:00', verbose_name='Giờ nhận phòng')
    check_out_time  = models.TimeField(default='12:00', verbose_name='Giờ trả phòng')

    is_active       = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Khách sạn'
        verbose_name_plural = 'Khách sạn'
        ordering            = ['-star_rating', 'name']
        indexes = [
            # Tương ứng: CREATE INDEX idx_hotel_location ON Hotel (latitude, longitude)
            models.Index(fields=['latitude', 'longitude'], name='idx_hotel_location'),
            models.Index(fields=['is_active'],             name='idx_hotel_active'),
            models.Index(fields=['city'],                  name='idx_hotel_city'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify_for_model(model=Hotel, value=self.name, instance_pk=self.pk)
        else:
            # Nếu user set slug nhưng bị trùng, tự append suffix
            existing = Hotel.objects.filter(slug=self.slug).exclude(pk=self.pk).exists()
            if existing:
                self.slug = unique_slugify_for_model(model=Hotel, value=self.slug, instance_pk=self.pk)
        super().save(*args, **kwargs)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def star_range(self):
        return range(self.star_rating)

    def distance_to(self, lat, lng):
        """Trả về khoảng cách km từ khách sạn đến tọa độ (lat, lng)."""
        return haversine_distance(
            float(self.latitude), float(self.longitude),
            float(lat), float(lng)
        )

    def thumbnail(self):
        """Trả về URL ảnh: ưu tiên file upload, fallback sang thumbnail_url."""
        if self.image:
            return self.image.url
        return self.thumbnail_url or ''

    def cheapest_room(self):
        """Giá phòng rẻ nhất trong khách sạn."""
        rt = self.room_types.filter(is_active=True).order_by('price_per_night').first()
        return rt.price_per_night if rt else None


# ─── 3. HotelImage ────────────────────────────────────────────────────────────

class HotelImage(models.Model):
    """Ảnh gallery của khách sạn."""
    hotel   = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images')
    image   = models.ImageField(upload_to='hotels/gallery/', verbose_name='Ảnh')
    caption = models.CharField(max_length=200, blank=True, verbose_name='Chú thích')
    order   = models.SmallIntegerField(default=0, verbose_name='Thứ tự hiển thị')

    class Meta:
        verbose_name        = 'Ảnh khách sạn'
        verbose_name_plural = 'Ảnh khách sạn'
        ordering            = ['order']

    def __str__(self):
        return f'Ảnh #{self.order} — {self.hotel.name}'


# ─── 4. RoomType ──────────────────────────────────────────────────────────────

class RoomType(models.Model):
    """
    Loại phòng (Standard / Deluxe / Suite / Family ...).
    Tương ứng bảng RoomType trong SQL schema.
    """
    BED_CHOICES = [
        ('single',  'Single (1 giường đơn)'),
        ('double',  'Double (1 giường đôi)'),
        ('twin',    'Twin (2 giường đơn)'),
        ('queen',   'Queen'),
        ('king',    'King'),
        ('bunk',    'Bunk (2 tầng)'),
        ('other',   'Khác'),
    ]

    hotel           = models.ForeignKey(
        Hotel, on_delete=models.CASCADE,
        related_name='room_types', verbose_name='Khách sạn'
    )
    name            = models.CharField(max_length=100, verbose_name='Tên loại phòng')
    description     = models.TextField(blank=True, verbose_name='Mô tả')
    max_occupancy   = models.SmallIntegerField(default=2, verbose_name='Sức chứa tối đa (người)')
    bed_type        = models.CharField(
        max_length=50, choices=BED_CHOICES,
        blank=True, verbose_name='Loại giường'
    )
    area_sqm        = models.DecimalField(
        max_digits=6, decimal_places=2,
        null=True, blank=True, verbose_name='Diện tích (m²)'
    )
    price_per_night = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name='Giá / đêm (VNĐ)'
    )
    thumbnail_url   = models.CharField(max_length=500, blank=True, verbose_name='URL ảnh')
    image           = models.ImageField(
        upload_to='rooms/', blank=True, null=True,
        verbose_name='Ảnh (upload)'
    )
    # Quan hệ N:N với Amenity — tương ứng bảng RoomAmenity
    amenities       = models.ManyToManyField(
        Amenity,
        through='RoomAmenity',
        related_name='room_types',
        blank=True,
        verbose_name='Tiện ích'
    )
    is_active       = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Loại phòng'
        verbose_name_plural = 'Loại phòng'
        ordering            = ['hotel', 'price_per_night']

    def __str__(self):
        return f'{self.hotel.name} — {self.name}'

    def thumbnail(self):
        if self.image:
            return self.image.url
        return self.thumbnail_url or ''

    def available_rooms_count(self):
        """Số phòng thực tế đang available."""
        return self.rooms.filter(status='available').count()


# ─── 5. RoomAmenity (bảng trung gian N:N) ────────────────────────────────────

class RoomAmenity(models.Model):
    """
    Bảng trung gian: RoomType ↔ Amenity (many-to-many).
    Tương ứng bảng RoomAmenity trong SQL schema.
    """
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, verbose_name='Loại phòng')
    amenity   = models.ForeignKey(Amenity,  on_delete=models.CASCADE, verbose_name='Tiện ích')

    class Meta:
        unique_together     = ('room_type', 'amenity')
        verbose_name        = 'Tiện ích phòng'
        verbose_name_plural = 'Tiện ích phòng'

    def __str__(self):
        return f'{self.room_type.name} — {self.amenity.name}'


# ─── 6. Room (Phòng thực tế) ─────────────────────────────────────────────────

class Room(models.Model):
    """
    Phòng thực tế (101, 202A, ...).
    Tương ứng bảng Room trong SQL schema.
    """
    STATUS_CHOICES = [
        ('available',    '✅ Còn trống'),
        ('occupied',     '🔴 Đang có khách'),
        ('maintenance',  '🔧 Đang bảo trì'),
    ]

    hotel        = models.ForeignKey(
        Hotel, on_delete=models.CASCADE,
        related_name='rooms', verbose_name='Khách sạn'
    )
    room_type    = models.ForeignKey(
        RoomType, on_delete=models.RESTRICT,
        related_name='rooms', verbose_name='Loại phòng'
    )
    room_number  = models.CharField(max_length=10, verbose_name='Số phòng')
    floor        = models.SmallIntegerField(null=True, blank=True, verbose_name='Tầng')
    status       = models.CharField(
        max_length=15, choices=STATUS_CHOICES,
        default='available', verbose_name='Trạng thái'
    )
    note         = models.TextField(blank=True, verbose_name='Ghi chú nội bộ')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Phòng'
        verbose_name_plural = 'Phòng'
        unique_together     = ('hotel', 'room_number')   # Số phòng không trùng trong hotel
        ordering            = ['hotel', 'floor', 'room_number']
        indexes = [
            models.Index(fields=['status'],   name='idx_room_status'),
            models.Index(fields=['hotel'],    name='idx_room_hotel'),
        ]

    def __str__(self):
        return f'Phòng {self.room_number} ({self.hotel.name})'
