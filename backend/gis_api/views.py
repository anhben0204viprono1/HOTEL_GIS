from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Hotel
from .serializers import HotelSerializer

@api_view(['GET'])
def search_hotels(request):
    city = request.GET.get('city')
    district = request.GET.get('district')

    hotels = Hotel.objects.filter(is_active=True)

    if city:
        hotels = hotels.filter(city__icontains=city)

    if district:
        hotels = hotels.filter(district__icontains=district)

    serializer = HotelSerializer(hotels, many=True)
    return Response(serializer.data)
