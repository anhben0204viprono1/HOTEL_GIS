from rest_framework import serializers
from .models import Hotel

class HotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = [
            'hotel_id',
            'name',
            'address',
            'city',
            'district',
            'latitude',
            'longitude',
            'star_rating'
        ]
