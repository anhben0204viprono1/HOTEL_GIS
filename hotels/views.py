from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Min
from .models import Hotel, HotelCategory
import json


def hotel_list(request):

    hotels = (
        Hotel.objects
        .filter(is_active=True)
        .prefetch_related('room_types__roomamenity_set__amenity')
        .annotate(min_price=Min('room_types__price_per_night'))
    )

    q = request.GET.get('q', '')
    city = request.GET.get('city', '')
    stars = request.GET.get('stars', '')
    max_price = request.GET.get('max_price', '')
    category_id = request.GET.get('category', '')

    if q:
        hotels = hotels.filter(
            Q(name__icontains=q) |
            Q(address__icontains=q) |
            Q(city__icontains=q)
        )

    if city:
        hotels = hotels.filter(city__icontains=city)

    if stars:
        hotels = hotels.filter(star_rating=stars)

    if max_price:
        hotels = hotels.filter(min_price__lte=max_price)

    if category_id:
        hotels = hotels.filter(category_id=category_id)

    features = []

    for h in hotels:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(h.longitude), float(h.latitude)]
            },
            "properties": {
                "id": h.id,
                "name": h.name,
                "stars": h.star_rating,
                "price": str(h.min_price) if h.min_price else "0",
                "address": h.address,
                "city": h.city,
                "url": f"/hotels/{h.slug}/",
            }
        })

    geojson = json.dumps({
        "type": "FeatureCollection",
        "features": features
    })

    cities = (
        Hotel.objects
        .filter(is_active=True)
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )

    categories = HotelCategory.objects.all()

    context = {
        'hotels': hotels,
        'geojson': geojson,
        'cities': cities,
        'categories': categories,
        'filters': {
            'q': q,
            'city': city,
            'stars': stars,
            'max_price': max_price,
            'category': category_id
        },
        'total': hotels.count(),
    }

    return render(request, 'hotels/hotel_list.html', context)

def hotel_detail(request, slug):

    hotel = get_object_or_404(
        Hotel.objects.prefetch_related(
            'room_types__roomamenity_set__amenity',
            'images'
        ),
        slug=slug,
        is_active=True
    )

    room_types = hotel.room_types.all()

    amenities = set()

    for rt in room_types:
        for ra in rt.roomamenity_set.all():
            amenities.add(ra.amenity)

    gallery = hotel.images.all()

    hotel_geojson = json.dumps({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(hotel.longitude), float(hotel.latitude)]
        },
        "properties": {
            "name": hotel.name,
            "address": hotel.address
        }
    })

    context = {
        "hotel": hotel,
        "room_types": room_types,
        "amenities": amenities,
        "gallery": gallery,
        "hotel_geojson": hotel_geojson
    }

    return render(request, "hotels/hotel_detail.html", context)