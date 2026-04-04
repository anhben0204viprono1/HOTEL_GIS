from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Min
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Hotel, RoomType, Amenity
import json


def hotel_list(request):
    hotels = Hotel.objects.filter(is_active=True).prefetch_related('room_types')

    q         = request.GET.get('q', '')
    city      = request.GET.get('city', '')
    stars     = request.GET.get('stars', '')
    max_price = request.GET.get('max_price', '')

    if q:
        hotels = hotels.filter(Q(name__icontains=q) | Q(address__icontains=q) | Q(city__icontains=q))
    if city:
        hotels = hotels.filter(city__icontains=city)
    if stars:
        hotels = hotels.filter(star_rating=stars)
    if max_price:
        hotels = hotels.annotate(min_price=Min('room_types__price_per_night')) \
                       .filter(min_price__lte=max_price)

    # Annotate giá rẻ nhất cho mỗi hotel
    hotels = hotels.annotate(min_price=Min('room_types__price_per_night'))

    features = []
    for h in hotels:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(h.longitude), float(h.latitude)]},
            "properties": {
                "id":      h.id,
                "name":    h.name,
                "stars":   h.star_rating,
                "price":   str(h.min_price or ''),
                "address": h.address,
                "city":    h.city,
                "url":     f"/hotels/{h.slug}/",
            }
        })
    geojson = json.dumps({"type": "FeatureCollection", "features": features})

    cities = Hotel.objects.filter(is_active=True).values_list('city', flat=True).distinct().order_by('city')

    context = {
        'hotels':   hotels,
        'geojson':  geojson,
        'cities':   cities,
        'filters':  {'q': q, 'city': city, 'stars': stars, 'max_price': max_price},
        'total':    hotels.count(),
    }
    return render(request, 'hotels/hotel_list.html', context)


def hotel_detail(request, slug):
    hotel      = get_object_or_404(Hotel, slug=slug, is_active=True)
    room_types = hotel.room_types.filter(is_active=True).prefetch_related('amenities')
    gallery    = hotel.images.all()

    # Gom tất cả tiện ích từ các RoomType (unique)
    amenity_ids = set()
    amenities_list = []
    for rt in room_types:
        for a in rt.amenities.all():
            if a.id not in amenity_ids:
                amenity_ids.add(a.id)
                amenities_list.append(a)

    # Giá rẻ nhất
    cheapest = room_types.order_by('price_per_night').first()

    context = {
        'hotel':      hotel,
        'room_types': room_types,
        'amenities':  amenities_list,
        'gallery':    gallery,
        'cheapest':   cheapest,
        # Truyền tọa độ an toàn dạng float để JS dùng
        'hotel_lat':  float(hotel.latitude),
        'hotel_lng':  float(hotel.longitude),
    }
    return render(request, 'hotels/hotel_detail.html', context)


@require_GET
def hotels_geojson_api(request):
    """
    API trả về GeoJSON markers cho bản đồ.
    Hỗ trợ filter giống trang list: q, city, stars, max_price
    """
    hotels = Hotel.objects.filter(is_active=True).prefetch_related('room_types')

    q = request.GET.get('q', '')
    city = request.GET.get('city', '')
    stars = request.GET.get('stars', '')
    max_price = request.GET.get('max_price', '')

    if q:
        hotels = hotels.filter(Q(name__icontains=q) | Q(address__icontains=q) | Q(city__icontains=q))
    if city:
        hotels = hotels.filter(city__icontains=city)
    if stars:
        hotels = hotels.filter(star_rating=stars)
    if max_price:
        hotels = hotels.annotate(min_price=Min('room_types__price_per_night')).filter(min_price__lte=max_price)

    hotels = hotels.annotate(min_price=Min('room_types__price_per_night'))

    features = []
    for h in hotels:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(h.longitude), float(h.latitude)]},
            "properties": {
                "id": h.id,
                "slug": h.slug,
                "name": h.name,
                "stars": h.star_rating,
                "price": str(h.min_price or ''),
                "address": h.address,
                "city": h.city,
                "thumbnail": h.thumbnail(),
                "url": f"/hotels/{h.slug}/",
            }
        })

    return JsonResponse({"type": "FeatureCollection", "features": features})
