from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Hotel, HotelCategory, RoomType, Amenity, HotelImage
from .forms_admin import HotelAdminForm


class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 1
    fields = ['name', 'price_per_night', 'capacity', 'total_rooms', 'image']


class AmenityInline(admin.TabularInline):
    model = Amenity
    extra = 2
    fields = ['icon']


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1
    fields = ['image', 'caption']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    form = HotelAdminForm

    list_display  = ['name', 'city', 'stars_display', 'price_per_night', 'coord_display', 'osm_link', 'is_active']
    list_filter   = ['stars', 'city', 'is_active', 'category']
    search_fields = ['name', 'address', 'city']
    list_editable = ['is_active']
    list_per_page = 20
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['coord_display', 'mini_map_preview', 'created_at']
    inlines = [RoomTypeInline, AmenityInline, HotelImageInline]

    fieldsets = (
        ('📋 Thông tin cơ bản', {
            'fields': ('name', 'slug', 'category', 'stars', 'is_active')
        }),
        ('📍 Vị trí & Địa chỉ', {
            'fields': ('address', 'city', 'latitude', 'longitude', 'coord_display', 'mini_map_preview'),
            'description': '👆 Click lên bản đồ để đặt vị trí · Chỉ chấp nhận tọa độ trong lãnh thổ Việt Nam',
        }),
        ('💰 Giá & Liên hệ', {
            'fields': ('price_per_night', 'phone', 'email', 'website')
        }),
        ('📝 Nội dung', {
            'fields': ('description', 'image')
        }),
        ('🕐 Hệ thống', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {'all': ['https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css']}
        js  = ['https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js']

    # ── List columns ──────────────────────────────────────────────────────────

    @admin.display(description='⭐')
    def stars_display(self, obj):
        return format_html(
            '<span style="color:#C9A84C;font-weight:700;">{}</span>',
            '★' * obj.stars
        )

    @admin.display(description='🌐 Tọa độ')
    def coord_display(self, obj):
        if obj.latitude and obj.longitude:
            lat = float(obj.latitude)
            lng = float(obj.longitude)

            return format_html(
                '<code style="font-size:12px;color:#15803d;">{}°N,&nbsp;{}°E</code>',
                f"{lat:.4f}", f"{lng:.4f}"
            )

        return mark_safe('<span style="color:#dc2626;font-size:12px;">⚠ Chưa có tọa độ</span>')
    @admin.display(description='🗺')
    def osm_link(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://www.openstreetmap.org/?mlat={}&mlon={}&zoom=15" target="_blank" '
                'style="color:#2563eb;font-size:11px;background:#eff6ff;padding:3px 8px;border-radius:4px;text-decoration:none;">📍 OSM</a>',
                obj.latitude, obj.longitude
            )
        return mark_safe('<span style="color:#9ca3af;">—</span>')

    # ── Readonly mini map (chỉ hiện sau khi đã lưu) ───────────────────────────

    @admin.display(description='📍 Bản đồ xác nhận (chỉ đọc)')
    def mini_map_preview(self, obj):
        # Chưa lưu lần nào hoặc chưa có tọa độ
        if not obj.pk or not obj.latitude or not obj.longitude:
            return mark_safe(
                '<em style="color:#9ca3af;font-size:13px;">'
                'Chưa có tọa độ — chọn trên bản đồ rồi nhấn <strong>Lưu</strong>. '
                'Mini map sẽ hiện sau khi lưu.</em>'
            )

        lat  = float(obj.latitude)
        lng  = float(obj.longitude)
        mid  = 'minimap_{}'.format(obj.pk)
        name = obj.name.replace("'", r"\'").replace('<', '&lt;').replace('>', '&gt;')
        addr = obj.address.replace("'", r"\'").replace('<', '&lt;').replace('>', '&gt;')
        osm  = 'https://www.openstreetmap.org/?mlat={}&mlon={}&zoom=15'.format(lat, lng)

        html = (
            '<div style="margin-top:6px;">'
            '<div id="{mid}" style="height:260px;border:2px solid #d1d5db;border-radius:10px;'
            'overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);"></div>'
            '<p style="font-size:11px;color:#6b7280;margin:6px 0 0;">'
            '<strong>{name}</strong> &nbsp;&middot;&nbsp; '
            '<code style="color:#15803d;">{lat:.4f}&deg;N, {lng:.4f}&deg;E</code>'
            ' &nbsp;&middot;&nbsp; '
            '<a href="{osm}" target="_blank" style="color:#2563eb;">M&#7903; OpenStreetMap &#8599;</a>'
            '</p></div>'
            '<script>'
            '(function(){{'
            '  function go(){{'
            '    if(typeof L==="undefined"){{setTimeout(go,200);return;}}'
            '    var el=document.getElementById("{mid}");'
            '    if(!el||el._leaflet_id)return;'
            '    var m=L.map("{mid}",{{zoomControl:true,scrollWheelZoom:false}})'
            '      .setView([{lat},{lng}],15);'
            '    L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",'
            '      {{attribution:"&copy; OpenStreetMap"}}).addTo(m);'
            '    var ic=L.divIcon({{'
            '      html:"<div style=\'background:#C9A84C;color:#0D0D0D;width:36px;height:36px;'
            'border-radius:50% 50% 50% 0;display:flex;align-items:center;justify-content:center;'
            'font-size:18px;transform:rotate(-45deg);box-shadow:0 3px 10px rgba(0,0,0,.3);'
            'border:2px solid #333;\'><span style=\'transform:rotate(45deg)\'>&#127968;</span></div>",'
            '      className:"",iconSize:[36,36],iconAnchor:[18,36],popupAnchor:[0,-36]'
            '    }});'
            '    L.marker([{lat},{lng}],{{icon:ic}}).addTo(m)'
            '      .bindPopup("<strong>{name}</strong><br>{addr}").openPopup();'
            '  }}'
            '  document.readyState==="loading"'
            '    ?document.addEventListener("DOMContentLoaded",go):go();'
            '}})();'
            '</script>'
        ).format(mid=mid, lat=lat, lng=lng, name=name, addr=addr, osm=osm)

        return mark_safe(html)


# ─── Other admins ──────────────────────────────────────────────────────────────

@admin.register(HotelCategory)
class HotelCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'hotel_count']

    @admin.display(description='Số KS')
    def hotel_count(self, obj):
        return format_html('<b style="color:#2563eb;">{}</b>', obj.hotel_set.count())


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'hotel', 'price_per_night', 'capacity', 'total_rooms']
    list_filter   = ['hotel__city']
    search_fields = ['name', 'hotel__name']


# ─── Branding ──────────────────────────────────────────────────────────────────

admin.site.site_header = mark_safe(
    '<span style="font-family:Georgia,serif;color:#C9A84C;letter-spacing:2px;">'
    '&#127968; Hotel GIS Admin</span>'
)
admin.site.site_title  = "Hotel GIS"
admin.site.index_title = "Bảng điều khiển quản trị"