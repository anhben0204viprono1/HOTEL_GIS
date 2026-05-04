from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Min, Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import date, timedelta
from .models import Hotel, RoomType, Amenity, haversine_distance
from .models import HomepageConfig
import json


# ══════════════════════════════════════════════════════════════════════════════
# TRANG DANH SÁCH KHÁCH SẠN
# ══════════════════════════════════════════════════════════════════════════════

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

    # FIX: annotate 1 lần duy nhất, filter sau
    hotels = hotels.annotate(
        min_price=Min('room_types__price_per_night'),
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews'),
    )

    if max_price:
        try:
            hotels = hotels.filter(min_price__lte=float(max_price))
        except ValueError:
            pass

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

    # Stats cho trang chủ
    from bookings.models import Booking
    stats = {
        'total_hotels':   Hotel.objects.filter(is_active=True).count(),
        'total_cities':   Hotel.objects.filter(is_active=True).values('city').distinct().count(),
        'total_bookings': Booking.objects.filter(status__in=['confirmed', 'checked_in', 'checked_out']).count(),
    }

    context = {
        'hotels':  hotels,
        'geojson': geojson,
        'cities':  cities,
        'filters': {'q': q, 'city': city, 'stars': stars, 'max_price': max_price},
        'total':   hotels.count(),
        'stats':   stats,
    }
    context['homepage_config'] = HomepageConfig.get()
    return render(request, 'hotels/hotel_list.html', context)

def about_us(request):
    from bookings.models import Booking

    stats = {
        'total_hotels':   Hotel.objects.filter(is_active=True).count(),
        'total_cities':   Hotel.objects.filter(is_active=True).values('city').distinct().count(),
        'total_bookings': Booking.objects.filter(status__in=['confirmed', 'checked_in', 'checked_out']).count(),
    }
    return render(request, 'hotels/about_us.html', {'stats': stats})


# ══════════════════════════════════════════════════════════════════════════════
# TRANG CHI TIẾT KHÁCH SẠN
# ══════════════════════════════════════════════════════════════════════════════

def hotel_detail(request, slug):
    from bookings.models import Review

    hotel      = get_object_or_404(Hotel, slug=slug, is_active=True)
    room_types = hotel.room_types.filter(is_active=True).prefetch_related('amenities', 'images')
    gallery    = hotel.images.all()

    # Gom tiện ích unique từ tất cả RoomType
    amenity_ids    = set()
    amenities_list = []
    for rt in room_types:
        for a in rt.amenities.all():
            if a.id not in amenity_ids:
                amenity_ids.add(a.id)
                amenities_list.append(a)

    cheapest = room_types.order_by('price_per_night').first()

    # Reviews + avg_rating
    reviews    = Review.objects.filter(hotel=hotel, is_visible=True).select_related('user').order_by('-created_at')[:10]
    avg_rating = Review.objects.filter(hotel=hotel, is_visible=True).aggregate(avg=Avg('rating'))['avg']
    review_count = Review.objects.filter(hotel=hotel, is_visible=True).count()

    # Khách sạn gần đó (< 3km, tối đa 4)
    all_hotels = Hotel.objects.filter(is_active=True).exclude(pk=hotel.pk)
    nearby = []
    for h in all_hotels:
        dist = haversine_distance(
            float(hotel.latitude), float(hotel.longitude),
            float(h.latitude),     float(h.longitude)
        )
        if dist < 3.0:
            h.distance = round(dist, 1)
            nearby.append(h)
    nearby.sort(key=lambda h: h.distance)
    nearby = nearby[:4]

    context = {
        'hotel':        hotel,
        'room_types':   room_types,
        'amenities':    amenities_list,
        'gallery':      gallery,
        'cheapest':     cheapest,
        'hotel_lat':    float(hotel.latitude),
        'hotel_lng':    float(hotel.longitude),
        # Reviews
        'reviews':      reviews,
        'avg_rating':   round(avg_rating, 1) if avg_rating else None,
        'review_count': review_count,
        # Nearby
        'nearby':       nearby,
    }
    return render(request, 'hotels/hotel_detail.html', context)


# ══════════════════════════════════════════════════════════════════════════════
# TRANG CHI TIẾT LOẠI PHÒNG + LỊCH TRỐNG/BẬN 60 NGÀY
# ══════════════════════════════════════════════════════════════════════════════

def room_type_detail(request, pk):
    from bookings.models import Booking

    room_type = get_object_or_404(RoomType, pk=pk, is_active=True)
    hotel     = room_type.hotel

    # Lịch trống/bận 60 ngày tới
    today    = date.today()
    end_date = today + timedelta(days=60)

    # Lấy tất cả booking đang active trong 60 ngày
    active_bookings = Booking.objects.filter(
        room__room_type=room_type,
        status__in=['pending', 'confirmed', 'checked_in'],
        check_in__lt=end_date,
        check_out__gt=today,
    ).values('check_in', 'check_out')

    # Tạo set ngày bận
    busy_dates = set()
    for b in active_bookings:
        d = b['check_in']
        while d < b['check_out']:
            busy_dates.add(d.isoformat())
            d += timedelta(days=1)

    # Tạo danh sách 60 ngày cho template
    calendar_days = []
    d = today
    while d < end_date:
        calendar_days.append({
            'date':      d,
            'iso':       d.isoformat(),
            'is_busy':   d.isoformat() in busy_dates,
            'is_today':  d == today,
            'weekday':   d.weekday(),
        })
        d += timedelta(days=1)

    # Số phòng còn khả dụng hôm nay
    booked_today = Booking.objects.filter(
        room__room_type=room_type,
        status__in=['pending', 'confirmed', 'checked_in'],
        check_in__lte=today,
        check_out__gt=today,
    ).values_list('room_id', flat=True)

    from hotels.models import Room, HomepageConfig
    available_now = Room.objects.filter(
        room_type=room_type, status='available'
    ).exclude(id__in=booked_today).count()

    context = {
        'room_type':     room_type,
        'hotel':         hotel,
        'calendar_days': calendar_days,
        'busy_dates':    list(busy_dates),
        'available_now': available_now,
        'today':         today,
    }
    return render(request, 'hotels/room_type_detail.html', context)


# ══════════════════════════════════════════════════════════════════════════════
# GeoJSON API
# ══════════════════════════════════════════════════════════════════════════════

@require_GET
def hotels_geojson_api(request):
    hotels = Hotel.objects.filter(is_active=True)

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

    hotels = hotels.annotate(min_price=Min('room_types__price_per_night'))

    if max_price:
        try:
            hotels = hotels.filter(min_price__lte=float(max_price))
        except ValueError:
            pass

    features = []
    for h in hotels:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(h.longitude), float(h.latitude)]},
            "properties": {
                "id":        h.id,
                "slug":      h.slug,
                "name":      h.name,
                "stars":     h.star_rating,
                "price":     str(h.min_price or ''),
                "address":   h.address,
                "city":      h.city,
                "thumbnail": h.thumbnail(),
                "url":       f"/hotels/{h.slug}/",
            }
        })

    return JsonResponse({"type": "FeatureCollection", "features": features})
