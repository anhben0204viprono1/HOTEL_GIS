from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt


def search_accommodation(request):
    """
    API giả lập tìm kiếm khách sạn / nhà nghỉ theo vị trí
    Sau này có thể thay bằng dữ liệu GIS thật (OSM, PostGIS)
    """

    query = request.GET.get("q", "")

    data = {
        "status": "ok",
        "query": query,
        "center": {
            "lat": 10.8700,
            "lng": 106.8000
        },
        "results": [
            {
                "name": "Khách sạn ABC",
                "type": "hotel",
                "lat": 10.8712,
                "lng": 106.8021
            },
            {
                "name": "Nhà nghỉ XYZ",
                "type": "guesthouse",
                "lat": 10.8689,
                "lng": 106.7983
            }
        ]
    }

    return JsonResponse(data)
from django.shortcuts import render


def home(request):
    return render(request, "index.html")
