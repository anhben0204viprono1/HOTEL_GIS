from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Hotel, Amenity, RoomType, RoomAmenity, Room, HotelImage
from .forms_admin import HotelAdminForm


# ─── Inlines ──────────────────────────────────────────────────────────────────

class HotelImageInline(admin.TabularInline):
    model  = HotelImage
    extra  = 1
    fields = ['image', 'caption', 'order']

class RoomTypeInline(admin.TabularInline):
    model  = RoomType
    extra  = 1
    fields = ['name', 'bed_type', 'max_occupancy', 'area_sqm', 'price_per_night', 'is_active']
    show_change_link = True

class RoomInline(admin.TabularInline):
    model  = Room
    extra  = 0
    fields = ['room_number', 'floor', 'room_type', 'status', 'note']
    show_change_link = True

class RoomAmenityInline(admin.TabularInline):
    model  = RoomAmenity
    extra  = 2
    fields = ['amenity']
    verbose_name        = 'Tiện ích'
    verbose_name_plural = 'Tiện ích phòng'


# ─── Hotel Admin ──────────────────────────────────────────────────────────────

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    form = HotelAdminForm

    list_display  = ['name', 'city', 'stars_display', 'cheapest_price', 'coord_display', 'osm_link', 'is_active']
    list_filter   = ['star_rating', 'city', 'is_active']
    search_fields = ['name', 'address', 'city']
    list_editable = ['is_active']
    list_per_page = 25
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields     = ['coord_display', 'mini_map_preview', 'created_at', 'updated_at']
    inlines = [RoomTypeInline, HotelImageInline]

    fieldsets = (
        ('📋 Thông tin cơ bản', {
            'fields': ('name', 'slug', 'star_rating', 'is_active')
        }),
        ('📍 Vị trí & Địa chỉ', {
            'fields': ('address', 'city', 'latitude', 'longitude', 'coord_display', 'mini_map_preview'),
            'description': '👆 Click lên bản đồ để đặt vị trí — chỉ nhận tọa độ trong Việt Nam',
        }),
        ('⏰ Giờ nhận / trả phòng', {
            'fields': ('check_in_time', 'check_out_time'),
        }),
        ('💰 Liên hệ', {
            'fields': ('phone', 'email', 'website')
        }),
        ('📝 Nội dung & Ảnh', {
            'fields': ('description', 'image', 'thumbnail_url')
        }),
        ('🕐 Hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {'all': ['https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css']}
        js  = ['https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js']

    @admin.display(description='⭐')
    def stars_display(self, obj):
        return format_html('<span style="color:#C9A84C;font-weight:700;">{}</span>', '★' * obj.star_rating)

    @admin.display(description='Giá từ')
    def cheapest_price(self, obj):
        price = obj.cheapest_room()
        if price:
            return format_html('<span style="color:#15803d;font-weight:600;">{:,.0f} ₫</span>', price)
        return mark_safe('<span style="color:#9ca3af;">—</span>')

    @admin.display(description='🌐 Tọa độ')
    def coord_display(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<code style="font-size:11px;color:#15803d;">{:.6f}°N, {:.6f}°E</code>',
                float(obj.latitude), float(obj.longitude)
            )
        return mark_safe('<span style="color:#dc2626;font-size:12px;">⚠ Chưa có</span>')

    @admin.display(description='🗺')
    def osm_link(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://www.openstreetmap.org/?mlat={}&mlon={}&zoom=16" target="_blank" '
                'style="color:#2563eb;font-size:11px;background:#eff6ff;padding:3px 8px;border-radius:4px;text-decoration:none;">📍 OSM</a>',
                obj.latitude, obj.longitude
            )
        return mark_safe('<span style="color:#9ca3af;">—</span>')

    @admin.display(description='📍 Bản đồ xác nhận')
    def mini_map_preview(self, obj):
        if not obj.pk or not obj.latitude or not obj.longitude:
            return mark_safe(
                '<em style="color:#9ca3af;font-size:13px;">'
                'Chưa có tọa độ — chọn trên bản đồ rồi nhấn <strong>Lưu</strong>.</em>'
            )
        lat  = float(obj.latitude)
        lng  = float(obj.longitude)
        mid  = 'minimap_{}'.format(obj.pk)
        name = obj.name.replace("'", r"\'").replace('<', '&lt;').replace('>', '&gt;')
        addr = obj.address.replace("'", r"\'").replace('<', '&lt;').replace('>', '&gt;')
        osm  = 'https://www.openstreetmap.org/?mlat={}&mlon={}&zoom=16'.format(lat, lng)
        html = (
            '<div style="margin-top:6px;">'
            '<div id="{mid}" style="height:260px;border:2px solid #d1d5db;border-radius:10px;'
            'overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);"></div>'
            '<p style="font-size:11px;color:#6b7280;margin:6px 0 0;">'
            '<strong>{name}</strong> &nbsp;&middot;&nbsp;'
            '<code style="color:#15803d;">{lat:.6f}&deg;N, {lng:.6f}&deg;E</code>'
            '&nbsp;&middot;&nbsp;'
            '<a href="{osm}" target="_blank" style="color:#2563eb;">M&#7903; OSM &#8599;</a>'
            '</p></div>'
            '<script>(function(){{'
            'function go(){{'
            'if(typeof L==="undefined"){{setTimeout(go,200);return;}}'
            'var el=document.getElementById("{mid}");'
            'if(!el||el._leaflet_id)return;'
            'var m=L.map("{mid}",{{zoomControl:true,scrollWheelZoom:false}}).setView([{lat},{lng}],16);'
            'L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",'
            '{{attribution:"&copy; OpenStreetMap"}}).addTo(m);'
            'var ic=L.divIcon({{'
            'html:"<div style=\'background:#C9A84C;color:#0D0D0D;width:36px;height:36px;'
            'border-radius:50%% 50%% 50%% 0;display:flex;align-items:center;justify-content:center;'
            'font-size:18px;transform:rotate(-45deg);box-shadow:0 3px 10px rgba(0,0,0,.3);'
            'border:2px solid #333;\'><span style=\'transform:rotate(45deg)\'>&#127968;</span></div>",'
            'className:"",iconSize:[36,36],iconAnchor:[18,36],popupAnchor:[0,-36]}});'
            'L.marker([{lat},{lng}],{{icon:ic}}).addTo(m)'
            '.bindPopup("<strong>{name}</strong><br>{addr}").openPopup();'
            '}}'
            'document.readyState==="loading"?document.addEventListener("DOMContentLoaded",go):go();'
            '}})();</script>'
        ).format(mid=mid, lat=lat, lng=lng, name=name, addr=addr, osm=osm)
        return mark_safe(html)


# ─── Amenity Admin ────────────────────────────────────────────────────────────

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'description']
    list_filter   = ['category']
    search_fields = ['name']


# ─── RoomType Admin ───────────────────────────────────────────────────────────

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'hotel', 'bed_type', 'max_occupancy', 'area_sqm', 'price_per_night', 'available_count', 'is_active']
    list_filter   = ['hotel__city', 'bed_type', 'is_active']
    search_fields = ['name', 'hotel__name']
    inlines       = [RoomAmenityInline]

    @admin.display(description='Phòng còn trống')
    def available_count(self, obj):
        count = obj.available_rooms_count()
        color = '#15803d' if count > 0 else '#dc2626'
        return format_html('<b style="color:{};">{}</b>', color, count)


# ─── Room Admin ───────────────────────────────────────────────────────────────

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display  = ['room_number', 'hotel', 'room_type', 'floor', 'status_display', 'note','status']
    list_filter   = ['status', 'hotel__city', 'floor']
    search_fields = ['room_number', 'hotel__name', 'room_type__name']
    list_editable = ['status']

    STATUS_COLORS = {
        'available':   '#15803d',
        'occupied':    '#dc2626',
        'maintenance': '#d97706',
    }

    @admin.display(description='Trạng thái')
    def status_display(self, obj):
        color = self.STATUS_COLORS.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )


# ─── Branding ─────────────────────────────────────────────────────────────────

admin.site.site_header = mark_safe(
    '<span style="font-family:Georgia,serif;color:#C9A84C;letter-spacing:2px;">&#127968; Hotel GIS Admin</span>'
)
admin.site.site_title  = 'Hotel GIS'
admin.site.index_title = 'Bảng điều khiển quản trị'