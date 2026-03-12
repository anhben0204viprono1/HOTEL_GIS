"""
Seed dữ liệu mẫu — dựa theo INSERT trong SQL schema thực tế.
Chạy: python manage.py seed_hotels
"""
from django.core.management.base import BaseCommand
from hotels.models import Hotel, Amenity, RoomType, RoomAmenity, Room
from django.utils.text import slugify
from decimal import Decimal

AMENITIES_DATA = [
    ('WiFi miễn phí',     'other',         'Kết nối WiFi tốc độ cao'),
    ('TV màn hình phẳng', 'entertainment', 'TV LED 40 inch trở lên'),
    ('Điều hòa',          'climate',       'Điều hòa 2 chiều'),
    ('Minibar',           'kitchen',       'Tủ lạnh minibar'),
    ('Máy pha cà phê',    'kitchen',       'Máy pha cà phê Nespresso'),
    ('Bồn tắm',           'bathroom',      'Bồn tắm nằm'),
    ('Vòi hoa sen',       'bathroom',      'Vòi sen tăng áp'),
    ('Két sắt',           'bedroom',       'Két sắt điện tử'),
    ('Ban công',          'other',         'Ban công riêng'),
    ('Netflix',           'entertainment', 'Tài khoản Netflix'),
]

HOTELS_DATA = [
    {
        'name': 'The Reverie Saigon',
        'address': '22-36 Nguyễn Huệ, Bến Nghé, Quận 1, TP.HCM',
        'city': 'Hồ Chí Minh',
        'lat': '10.77378600', 'lng': '106.70454926',
        'phone': '02838236688', 'email': 'info@thereveriesaigon.com',
        'star_rating': 5,
        'desc': 'Khách sạn sang trọng tại trung tâm TP.HCM',
        'website': 'https://www.thereveriesaigon.com',
        'rooms': [
            {'name':'Deluxe Room','bed':'double','capacity':2,'area':35,'price':3200000,'count':20},
            {'name':'Premier Suite','bed':'king','capacity':3,'area':65,'price':6500000,'count':8},
            {'name':'Presidential Suite','bed':'king','capacity':4,'area':120,'price':15000000,'count':2},
        ]
    },
    {
        'name': 'Rex Hotel',
        'address': '141 Nguyễn Huệ, Bến Nghé, Quận 1, TP.HCM',
        'city': 'Hồ Chí Minh',
        'lat': '10.77586934', 'lng': '106.70126429',
        'phone': '02838222222', 'email': 'info@rexhotel.com',
        'star_rating': 4,
        'desc': 'Khách sạn biểu tượng lịch sử Sài Gòn',
        'website': 'https://www.rexhotel.com',
        'rooms': [
            {'name':'Standard Room','bed':'twin','capacity':2,'area':28,'price':1800000,'count':30},
            {'name':'Superior Room','bed':'double','capacity':2,'area':35,'price':2400000,'count':20},
            {'name':'Junior Suite','bed':'king','capacity':3,'area':55,'price':4500000,'count':6},
        ]
    },
    {
        'name': 'Park Hyatt Saigon',
        'address': '2 Công Trường Lam Sơn, Bến Nghé, Quận 1, TP.HCM',
        'city': 'Hồ Chí Minh',
        'lat': '10.77776170', 'lng': '106.70338423',
        'phone': '02838233333', 'email': 'info@parkhyattsaigon.com',
        'star_rating': 5,
        'desc': 'Khách sạn cao cấp 5 sao giữa trung tâm Sài Gòn',
        'website': 'https://www.parkhyattsaigon.com',
        'rooms': [
            {'name':'Park Room','bed':'double','capacity':2,'area':40,'price':4200000,'count':25},
            {'name':'Park Suite','bed':'king','capacity':3,'area':80,'price':8500000,'count':8},
        ]
    },
    {
        'name': 'Mai House Saigon',
        'address': '1-3-5 Ngô Thời Nhiệm, Phường 6, Quận 3, TP.HCM',
        'city': 'Hồ Chí Minh',
        'lat': '10.78209958', 'lng': '106.69159148',
        'phone': '02838355555', 'email': 'info@maihousesaigon.com',
        'star_rating': 4,
        'desc': 'Khách sạn boutique phong cách Đông Dương hiện đại',
        'website': 'https://www.maihousesaigon.com',
        'rooms': [
            {'name':'Classic Room','bed':'double','capacity':2,'area':30,'price':2100000,'count':15},
            {'name':'Deluxe Room','bed':'king','capacity':2,'area':42,'price':2800000,'count':10},
        ]
    },
    {
        'name': 'Vinpearl Landmark 81',
        'address': '720A Điện Biên Phủ, Phường 22, Bình Thạnh, TP.HCM',
        'city': 'Hồ Chí Minh',
        'lat': '10.79523603', 'lng': '106.72188840',
        'phone': '02838433333', 'email': 'info@vinpearllandmark81.com',
        'star_rating': 5,
        'desc': 'Khách sạn trên tòa nhà cao nhất Việt Nam',
        'website': 'https://www.vinpearl.com',
        'rooms': [
            {'name':'Sky Room','bed':'king','capacity':2,'area':45,'price':5500000,'count':30},
            {'name':'Sky Suite','bed':'king','capacity':3,'area':90,'price':12000000,'count':10},
        ]
    },
    {
        'name': 'Holiday Inn & Suites',
        'address': '18E Cộng Hòa, Tân Bình, TP.HCM',
        'city': 'Hồ Chí Minh',
        'lat': '10.80165237', 'lng': '106.65506175',
        'phone': '02838466666', 'email': 'info@holidayinnandsuites.com',
        'star_rating': 4,
        'desc': 'Khách sạn hiện đại gần sân bay Tân Sơn Nhất',
        'website': 'https://www.ihg.com',
        'rooms': [
            {'name':'Standard Room','bed':'twin','capacity':2,'area':28,'price':1600000,'count':40},
            {'name':'Suite','bed':'king','capacity':4,'area':60,'price':3200000,'count':10},
        ]
    },
]


class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu khách sạn theo schema mới'

    def handle(self, *args, **kwargs):
        self.stdout.write('📦 Tạo tiện ích...')
        amenity_objs = []
        for name, cat, desc in AMENITIES_DATA:
            a, _ = Amenity.objects.get_or_create(name=name, defaults={'category':cat,'description':desc})
            amenity_objs.append(a)

        self.stdout.write('🏨 Tạo khách sạn...')
        for data in HOTELS_DATA:
            hotel, created = Hotel.objects.get_or_create(
                slug=slugify(data['name']),
                defaults={
                    'name': data['name'],
                    'address':     data['address'],
                    'city':        data['city'],
                    'latitude':    data['lat'],
                    'longitude':   data['lng'],
                    'phone':       data['phone'],
                    'email':       data['email'],
                    'star_rating': data['star_rating'],
                    'description': data['desc'],
                    'website':     data['website'],
                }
            )
            if not created:
                self.stdout.write(f'  ⏭ Đã tồn tại: {hotel.name}')
                continue

            # Tạo RoomType + Room thực tế
            for i, r in enumerate(data['rooms']):
                rt = RoomType.objects.create(
                    hotel=hotel,
                    name=r['name'],
                    bed_type=r['bed'],
                    max_occupancy=r['capacity'],
                    area_sqm=r['area'],
                    price_per_night=r['price'],
                )
                # Gắn một số tiện ích mẫu
                for a in amenity_objs[:5]:
                    RoomAmenity.objects.get_or_create(room_type=rt, amenity=a)

                # Tạo phòng thực tế
                for j in range(1, r['count'] + 1):
                    floor  = (j // 10) + 1
                    number = f'{floor}{j:02d}'
                    Room.objects.get_or_create(
                        hotel=hotel,
                        room_number=number,
                        defaults={'room_type': rt, 'floor': floor, 'status': 'available'}
                    )

            self.stdout.write(self.style.SUCCESS(f'  ✅ {hotel.name}'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Seed hoàn tất!'))