from django.core.management.base import BaseCommand
from hotels.models import Hotel, HotelCategory, RoomType, Amenity


HOTELS_DATA = [
    {
        "name": "Grand Saigon Palace",
        "slug": "grand-saigon-palace",
        "address": "12 Lê Lợi, Quận 1",
        "city": "Hồ Chí Minh",
        "lat": 10.7769, "lng": 106.7009,
        "stars": 5, "price": 4800000,
        "desc": "Khách sạn sang trọng bậc nhất trung tâm Sài Gòn, tầm nhìn toàn cảnh thành phố.",
        "phone": "028 3823 4999",
        "amenities": ["wifi", "pool", "gym", "spa", "restaurant", "parking", "bar", "breakfast"],
        "rooms": [
            {"name": "Deluxe Room", "price": 2400000, "capacity": 2, "total": 20},
            {"name": "Premier Suite", "price": 4800000, "capacity": 3, "total": 10},
            {"name": "Presidential Suite", "price": 9600000, "capacity": 4, "total": 3},
        ]
    },
    {
        "name": "Riverside Boutique Hotel",
        "slug": "riverside-boutique-hotel",
        "address": "45 Bến Bạch Đằng, Quận 1",
        "city": "Hồ Chí Minh",
        "lat": 10.7755, "lng": 106.7053,
        "stars": 4, "price": 2200000,
        "desc": "Khách sạn boutique bên sông Sài Gòn, phong cách Đông Dương hiện đại.",
        "phone": "028 3910 5000",
        "amenities": ["wifi", "restaurant", "bar", "breakfast", "laundry"],
        "rooms": [
            {"name": "Standard Room", "price": 1500000, "capacity": 2, "total": 30},
            {"name": "River View Room", "price": 2200000, "capacity": 2, "total": 15},
            {"name": "Penthouse Suite", "price": 5500000, "capacity": 4, "total": 2},
        ]
    },
    {
        "name": "Danang Beachfront Resort",
        "slug": "danang-beachfront-resort",
        "address": "122 Võ Nguyên Giáp, Ngũ Hành Sơn",
        "city": "Đà Nẵng",
        "lat": 16.0016, "lng": 108.2463,
        "stars": 5, "price": 3500000,
        "desc": "Resort 5 sao trên bãi biển Mỹ Khê đẹp nhất Đà Nẵng, trải nghiệm nghỉ dưỡng đẳng cấp.",
        "phone": "0236 396 8888",
        "amenities": ["wifi", "pool", "gym", "spa", "restaurant", "beach", "bar", "airport", "breakfast"],
        "rooms": [
            {"name": "Garden View Room", "price": 2200000, "capacity": 2, "total": 40},
            {"name": "Ocean View Room", "price": 3500000, "capacity": 2, "total": 25},
            {"name": "Beach Villa", "price": 8000000, "capacity": 4, "total": 8},
        ]
    },
    {
        "name": "Hoi An Ancient House Hotel",
        "slug": "hoi-an-ancient-house",
        "address": "18 Trần Phú, Phố Cổ",
        "city": "Hội An",
        "lat": 15.8801, "lng": 108.3380,
        "stars": 4, "price": 1800000,
        "desc": "Khách sạn nằm giữa lòng phố cổ Hội An di sản UNESCO, kiến trúc truyền thống.",
        "phone": "0235 386 1445",
        "amenities": ["wifi", "pool", "restaurant", "breakfast", "laundry", "spa"],
        "rooms": [
            {"name": "Heritage Room", "price": 1200000, "capacity": 2, "total": 20},
            {"name": "Deluxe Garden", "price": 1800000, "capacity": 2, "total": 10},
            {"name": "Ancient House Suite", "price": 3500000, "capacity": 3, "total": 4},
        ]
    },
    {
        "name": "Hanoi Imperial Hotel",
        "slug": "hanoi-imperial-hotel",
        "address": "56 Hàng Bài, Hoàn Kiếm",
        "city": "Hà Nội",
        "lat": 21.0285, "lng": 105.8542,
        "stars": 5, "price": 5200000,
        "desc": "Khách sạn hạng sang trung tâm Hà Nội, phong cách kiến trúc Pháp cổ điển.",
        "phone": "024 3936 6888",
        "amenities": ["wifi", "gym", "spa", "restaurant", "parking", "bar", "ac", "breakfast", "laundry"],
        "rooms": [
            {"name": "Classic Room", "price": 2800000, "capacity": 2, "total": 35},
            {"name": "Deluxe Suite", "price": 5200000, "capacity": 3, "total": 12},
            {"name": "Royal Suite", "price": 12000000, "capacity": 4, "total": 2},
        ]
    },
    {
        "name": "Nha Trang Ocean Star",
        "slug": "nha-trang-ocean-star",
        "address": "38 Trần Phú, Lộc Thọ",
        "city": "Nha Trang",
        "lat": 12.2388, "lng": 109.1967,
        "stars": 4, "price": 2100000,
        "desc": "Khách sạn view biển Nha Trang xanh ngắt, sát bãi biển đẹp nhất miền Trung.",
        "phone": "0258 352 8888",
        "amenities": ["wifi", "pool", "restaurant", "beach", "bar", "breakfast", "parking"],
        "rooms": [
            {"name": "Standard Sea View", "price": 1600000, "capacity": 2, "total": 30},
            {"name": "Deluxe Balcony", "price": 2100000, "capacity": 2, "total": 20},
            {"name": "Ocean Suite", "price": 4500000, "capacity": 4, "total": 5},
        ]
    },
]


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu khách sạn"

    def handle(self, *args, **kwargs):
        cat, _ = HotelCategory.objects.get_or_create(name="Resort & Spa")
        cat2, _ = HotelCategory.objects.get_or_create(name="Boutique Hotel")
        cat3, _ = HotelCategory.objects.get_or_create(name="Business Hotel")

        cats = [cat, cat, cat2, cat2, cat3, cat]

        for i, data in enumerate(HOTELS_DATA):
            hotel, created = Hotel.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    'name': data['name'],
                    'category': cats[i],
                    'address': data['address'],
                    'city': data['city'],
                    'latitude': data['lat'],
                    'longitude': data['lng'],
                    'stars': data['stars'],
                    'price_per_night': data['price'],
                    'description': data['desc'],
                    'phone': data['phone'],
                }
            )
            if created:
                for icon in data['amenities']:
                    Amenity.objects.get_or_create(hotel=hotel, icon=icon)
                for r in data['rooms']:
                    RoomType.objects.get_or_create(
                        hotel=hotel, name=r['name'],
                        defaults={
                            'price_per_night': r['price'],
                            'capacity': r['capacity'],
                            'total_rooms': r['total']
                        }
                    )
                self.stdout.write(self.style.SUCCESS(f"✅ Tạo: {hotel.name}"))
            else:
                self.stdout.write(f"⏭ Đã tồn tại: {hotel.name}")

        self.stdout.write(self.style.SUCCESS("\n🎉 Seed hoàn tất! 6 khách sạn đã được tạo."))