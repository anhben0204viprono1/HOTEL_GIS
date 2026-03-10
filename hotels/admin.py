from django.contrib import admin
from .models import Hotel, HotelCategory, RoomType, Amenity, HotelImage


class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 1


class AmenityInline(admin.TabularInline):
    model = Amenity
    extra = 1


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'stars', 'price_per_night', 'is_active']
    list_filter = ['stars', 'city', 'is_active', 'category']
    search_fields = ['name', 'address', 'city']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [RoomTypeInline, AmenityInline, HotelImageInline]
    list_editable = ['is_active']


@admin.register(HotelCategory)
class HotelCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


admin.site.site_header = "🏨 Hotel GIS Admin"
admin.site.site_title = "Hotel GIS"
admin.site.index_title = "Quản lý hệ thống khách sạn"