from django.http import JsonResponse
from .models import Hotel

def search_hotels(request):
    keyword = request.GET.get("q", "")

    hotels = Hotel.objects.filter(
        name__icontains=keyword,
        is_active=True
    )

    data = [
        {
            "id": h.hotel_id,
            "name": h.name,
            "address": h.address,
            "lat": float(h.latitude),
            "lng": float(h.longitude),
            "star": float(h.star_rating) if h.star_rating else None,
        }
        for h in hotels
    ]

    return JsonResponse(data, safe=False)
