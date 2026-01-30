from django.http import JsonResponse
import math

# Hàm tính khoảng cách Haversine (km)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # bán kính Trái Đất (km)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def search_accommodation(request):
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")

    if lat is None or lng is None:
        return JsonResponse({
            "status": "error",
            "message": "Missing lat or lng"
        }, status=400)

    lat = float(lat)
    lng = float(lng)

    return JsonResponse({
        "status": "ok",
        "lat": lat,
        "lng": lng
    })