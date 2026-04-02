"""
dashboard/views.py
Trang admin tự xây — yêu cầu staff hoặc superuser.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta, date
import json

from hotels.models import Hotel, RoomType, Room, Amenity, HotelImage, RoomTypeImage
from bookings.models import Booking, Payment, Review
from django.contrib.auth.models import User
from hotels.widgets import LeafletMapWidget


# ── Guard: chỉ staff/superuser mới vào được ──────────────────────────────────
def is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

staff_required = user_passes_test(is_staff, login_url='/accounts/login/')


# ═══════════════════════════════════════════════════════════
# DASHBOARD — Trang chủ admin
# ═══════════════════════════════════════════════════════════
@login_required
@staff_required
def dashboard_home(request):
    today = date.today()
    month_start = today.replace(day=1)

    # Thống kê tổng quan
    stats = {
        'total_hotels':   Hotel.objects.filter(is_active=True).count(),
        'total_rooms':    Room.objects.filter(status='available').count(),
        'total_users':    User.objects.filter(is_active=True, is_staff=False).count(),
        'total_bookings': Booking.objects.count(),

        # Tháng này
        'bookings_month': Booking.objects.filter(created_at__gte=month_start).count(),
        'revenue_month':  Payment.objects.filter(
            status='paid', paid_at__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0,

        # Hôm nay
        'checkin_today':  Booking.objects.filter(check_in=today, status='confirmed').count(),
        'checkout_today': Booking.objects.filter(check_out=today, status='checked_in').count(),
        'pending':        Booking.objects.filter(status='pending').count(),
    }

    # Booking 7 ngày gần nhất (cho chart)
    chart_labels, chart_data = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime('%d/%m'))
        chart_data.append(
            Booking.objects.filter(created_at__date=d).count()
        )

    # Booking mới nhất
    recent_bookings = (
        Booking.objects
        .select_related('user', 'room__room_type__hotel')
        .order_by('-created_at')[:8]
    )

    # Khách sạn được đặt nhiều nhất
    top_hotels = (
        Hotel.objects
        .annotate(booking_count=Count('rooms__bookings'))
        .order_by('-booking_count')[:5]
    )

    context = {
        'stats':           stats,
        'chart_labels':    json.dumps(chart_labels),
        'chart_data':      json.dumps(chart_data),
        'recent_bookings': recent_bookings,
        'top_hotels':      top_hotels,
        'page': 'dashboard',
    }
    return render(request, 'dashboard/home.html', context)


# ═══════════════════════════════════════════════════════════
# HOTELS — Quản lý khách sạn
# ═══════════════════════════════════════════════════════════
@login_required
@staff_required
def hotel_list(request):
    q      = request.GET.get('q', '')
    city   = request.GET.get('city', '')
    hotels = Hotel.objects.annotate(
        room_count=Count('rooms', distinct=True),
        booking_count=Count('rooms__bookings', distinct=True),
    ).order_by('-star_rating', 'name')

    if q:
        hotels = hotels.filter(Q(name__icontains=q) | Q(address__icontains=q))
    if city:
        hotels = hotels.filter(city__icontains=city)

    cities = Hotel.objects.values_list('city', flat=True).distinct()
    return render(request, 'dashboard/hotels/list.html', {
        'hotels': hotels, 'cities': cities,
        'filters': {'q': q, 'city': city}, 'page': 'hotels',
    })


@login_required
@staff_required
def hotel_create(request):
    if request.method == 'POST':
        return _save_hotel(request, None)
    amenities = Amenity.objects.all()
    return render(request, 'dashboard/hotels/form.html', {
        'amenities': amenities, 'page': 'hotels', 'action': 'Thêm mới',
    })


@login_required
@staff_required
def hotel_edit(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        return _save_hotel(request, hotel)
    amenities = Amenity.objects.all()
    return render(request, 'dashboard/hotels/form.html', {
        'hotel': hotel, 'amenities': amenities,
        'page': 'hotels', 'action': 'Chỉnh sửa',
    })


@login_required
@staff_required
def hotel_delete(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'POST':
        name = hotel.name
        hotel.delete()
        messages.success(request, f'Đã xóa khách sạn "{name}".')
    return redirect('dashboard:hotel_list')


@login_required
@staff_required
def hotel_toggle(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    hotel.is_active = not hotel.is_active
    hotel.save()
    status = 'kích hoạt' if hotel.is_active else 'ẩn'
    messages.success(request, f'Đã {status} khách sạn "{hotel.name}".')
    return redirect('dashboard:hotel_list')


def _save_hotel(request, hotel):
    """Helper lưu hotel từ POST data."""
    from django.utils.text import slugify
    data = request.POST

    try:
        lat = float(data.get('latitude', 0))
        lng = float(data.get('longitude', 0))
    except ValueError:
        messages.error(request, 'Tọa độ không hợp lệ.')
        return redirect('dashboard:hotel_list')

    fields = {
        'name':           data.get('name', '').strip(),
        'address':        data.get('address', '').strip(),
        'city':           data.get('city', '').strip(),
        'latitude':       lat,
        'longitude':      lng,
        'phone':          data.get('phone', '').strip(),
        'email':          data.get('email', '').strip(),
        'website':        data.get('website', '').strip(),
        'star_rating':    int(data.get('star_rating', 3)),
        'description':    data.get('description', '').strip(),
        'check_in_time':  data.get('check_in_time', '14:00'),
        'check_out_time': data.get('check_out_time', '12:00'),
        'is_active':      data.get('is_active') == 'on',
    }

    if not fields['name']:
        messages.error(request, 'Tên khách sạn không được để trống.')
        return redirect('dashboard:hotel_list')

    if hotel:
        for k, v in fields.items():
            setattr(hotel, k, v)
        if not hotel.slug:
            hotel.slug = slugify(hotel.name, allow_unicode=True)
        hotel.save()
        messages.success(request, f'Đã cập nhật khách sạn "{hotel.name}".')
    else:
        fields['slug'] = slugify(fields['name'], allow_unicode=True)
        hotel = Hotel(**fields)
        hotel.save()
        messages.success(request, f'Đã thêm khách sạn "{hotel.name}".')

    # ── Xử lý ảnh đại diện chính (1 file)
    if 'image_main' in request.FILES:
        hotel.image = request.FILES['image_main']
        hotel.save(update_fields=['image'])

    # ── Xử lý ảnh đính kèm (nhiều file)
    gallery_files  = request.FILES.getlist('gallery_images')
    gallery_caps   = request.POST.getlist('gallery_captions')
    delete_img_ids = request.POST.getlist('delete_image_ids')

    # Xóa ảnh được đánh dấu xóa
    if delete_img_ids:
        HotelImage.objects.filter(id__in=delete_img_ids, hotel=hotel).delete()

    # Đặt lại ảnh đại diện gallery
    primary_id = request.POST.get('primary_image_id')
    if primary_id:
        HotelImage.objects.filter(hotel=hotel).update(is_primary=False)
        HotelImage.objects.filter(id=primary_id, hotel=hotel).update(is_primary=True)

    # Upload ảnh mới
    for i, f in enumerate(gallery_files):
        cap = gallery_caps[i] if i < len(gallery_caps) else ''
        HotelImage.objects.create(hotel=hotel, image=f, caption=cap, order=i)

    return redirect('dashboard:hotel_list')


# ═══════════════════════════════════════════════════════════
# BOOKINGS — Quản lý đặt phòng
# ═══════════════════════════════════════════════════════════
@login_required
@staff_required
def booking_list(request):
    status = request.GET.get('status', '')
    q      = request.GET.get('q', '')

    bookings = (
        Booking.objects
        .select_related('user', 'room__room_type__hotel')
        .order_by('-created_at')
    )
    if status:
        bookings = bookings.filter(status=status)
    if q:
        bookings = bookings.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(room__hotel__name__icontains=q)
        )

    return render(request, 'dashboard/bookings/list.html', {
        'bookings': bookings,
        'filters':  {'status': status, 'q': q},
        'status_choices': Booking.STATUS_CHOICES,
        'page': 'bookings',
    })


@login_required
@staff_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'room__room_type__hotel'),
        pk=pk
    )
    return render(request, 'dashboard/bookings/detail.html', {
        'booking': booking, 'page': 'bookings',
    })


@login_required
@staff_required
def booking_update_status(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid = [s[0] for s in Booking.STATUS_CHOICES]
        if new_status in valid:
            booking.status = new_status
            if new_status == 'cancelled':
                booking.cancelled_at = timezone.now()
            booking.save()
            messages.success(request, f'Đã cập nhật trạng thái booking #{pk}.')
    return redirect('dashboard:booking_detail', pk=pk)


# ═══════════════════════════════════════════════════════════
# ROOMS — Quản lý phòng
# ═══════════════════════════════════════════════════════════
@login_required
@staff_required
def room_list(request):
    hotel_id = request.GET.get('hotel', '')
    status   = request.GET.get('status', '')

    rooms = Room.objects.select_related('hotel', 'room_type').order_by('hotel', 'room_number')
    if hotel_id:
        rooms = rooms.filter(hotel_id=hotel_id)
    if status:
        rooms = rooms.filter(status=status)

    hotels = Hotel.objects.filter(is_active=True)
    return render(request, 'dashboard/rooms/list.html', {
        'rooms':   rooms,
        'hotels':  hotels,
        'filters': {'hotel': hotel_id, 'status': status},
        'status_choices': Room.STATUS_CHOICES,
        'page': 'rooms',
    })


@login_required
@staff_required
def room_update_status(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.status = request.POST.get('status', room.status)
        room.save()
        messages.success(request, f'Đã cập nhật phòng {room.room_number}.')
    return redirect('dashboard:room_list')


# ═══════════════════════════════════════════════════════════
# USERS — Quản lý tài khoản
# ═══════════════════════════════════════════════════════════
@login_required
@staff_required
def user_list(request):
    q = request.GET.get('q', '')
    users = User.objects.annotate(
        booking_count=Count('bookings')
    ).order_by('-date_joined')

    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q)
        )

    return render(request, 'dashboard/users/list.html', {
        'users': users, 'q': q, 'page': 'users',
    })


@login_required
@staff_required
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user != request.user:
        user.is_active = not user.is_active
        user.save()
        status = 'kích hoạt' if user.is_active else 'khóa'
        messages.success(request, f'Đã {status} tài khoản "{user.username}".')
    return redirect('dashboard:user_list')


# ═══════════════════════════════════════════════════════════
# ROOM TYPES — Quản lý loại phòng
# ═══════════════════════════════════════════════════════════
@login_required
@staff_required
def roomtype_list(request, hotel_pk):
    hotel      = get_object_or_404(Hotel, pk=hotel_pk)
    room_types = hotel.room_types.prefetch_related('amenities').annotate(
        room_count=Count('rooms'),
        available_count=Count('rooms', filter=Q(rooms__status='available')),
    )
    return render(request, 'dashboard/rooms/roomtype_list.html', {
        'hotel': hotel, 'room_types': room_types, 'page': 'rooms',
    })


@login_required
@staff_required
def roomtype_create(request, hotel_pk):
    hotel = get_object_or_404(Hotel, pk=hotel_pk)
    if request.method == 'POST':
        return _save_roomtype(request, hotel, None)
    amenities = Amenity.objects.all().order_by('category', 'name')
    return render(request, 'dashboard/rooms/roomtype_form.html', {
        'hotel': hotel, 'amenities': amenities,
        'bed_choices': RoomType.BED_CHOICES, 'rt_images': [],
        'page': 'rooms', 'action': 'Thêm loại phòng',
    })


@login_required
@staff_required
def roomtype_edit(request, hotel_pk, pk):
    hotel     = get_object_or_404(Hotel, pk=hotel_pk)
    room_type = get_object_or_404(RoomType, pk=pk, hotel=hotel)
    if request.method == 'POST':
        return _save_roomtype(request, hotel, room_type)
    amenities         = Amenity.objects.all().order_by('category', 'name')
    selected_amenities = list(room_type.amenities.values_list('id', flat=True))
    rt_images          = room_type.images.all()
    return render(request, 'dashboard/rooms/roomtype_form.html', {
        'hotel': hotel, 'room_type': room_type,
        'amenities': amenities, 'selected_amenities': selected_amenities,
        'bed_choices': RoomType.BED_CHOICES, 'rt_images': rt_images,
        'page': 'rooms', 'action': 'Sửa loại phòng',
    })


@login_required
@staff_required
def roomtype_delete(request, hotel_pk, pk):
    hotel     = get_object_or_404(Hotel, pk=hotel_pk)
    room_type = get_object_or_404(RoomType, pk=pk, hotel=hotel)
    if request.method == 'POST':
        if room_type.rooms.exists():
            messages.error(request, f'Không thể xóa — loại phòng "{room_type.name}" còn {room_type.rooms.count()} phòng thực tế.')
        else:
            name = room_type.name
            room_type.delete()
            messages.success(request, f'Đã xóa loại phòng "{name}".')
    return redirect('dashboard:roomtype_list', hotel_pk=hotel_pk)


def _save_roomtype(request, hotel, room_type):
    from hotels.models import RoomAmenity
    data = request.POST
    try:
        price     = float(data.get('price_per_night', 0))
        occupancy = int(data.get('max_occupancy', 2))
        area      = float(data.get('area_sqm', 0)) if data.get('area_sqm') else None
    except ValueError:
        messages.error(request, 'Dữ liệu không hợp lệ.')
        return redirect('dashboard:roomtype_list', hotel_pk=hotel.pk)

    fields = {
        'hotel':           hotel,
        'name':            data.get('name', '').strip(),
        'description':     data.get('description', '').strip(),
        'bed_type':        data.get('bed_type', ''),
        'max_occupancy':   occupancy,
        'area_sqm':        area,
        'price_per_night': price,
        'is_active':       data.get('is_active') == 'on',
    }

    if not fields['name']:
        messages.error(request, 'Tên loại phòng không được để trống.')
        return redirect('dashboard:roomtype_list', hotel_pk=hotel.pk)

    if room_type:
        for k, v in fields.items():
            setattr(room_type, k, v)
        room_type.save()
    else:
        room_type = RoomType(**fields)
        room_type.save()

    # ── Ảnh đại diện chính
    if 'image_main' in request.FILES:
        room_type.image = request.FILES['image_main']
        room_type.save(update_fields=['image'])

    # ── Ảnh đính kèm
    gallery_files  = request.FILES.getlist('rt_gallery_images')
    gallery_caps   = request.POST.getlist('rt_gallery_captions')
    delete_img_ids = request.POST.getlist('delete_rt_image_ids')
    if delete_img_ids:
        RoomTypeImage.objects.filter(id__in=delete_img_ids, room_type=room_type).delete()
    primary_id = request.POST.get('primary_rt_image_id')
    if primary_id:
        RoomTypeImage.objects.filter(room_type=room_type).update(is_primary=False)
        RoomTypeImage.objects.filter(id=primary_id, room_type=room_type).update(is_primary=True)
    for i, f in enumerate(gallery_files):
        cap = gallery_caps[i] if i < len(gallery_caps) else ''
        RoomTypeImage.objects.create(room_type=room_type, image=f, caption=cap, order=i)

    # Cập nhật tiện ích M2M
    selected_ids = [int(x) for x in data.getlist('amenities') if x.isdigit()]
    RoomAmenity.objects.filter(room_type=room_type).delete()
    for aid in selected_ids:
        try:
            amenity = Amenity.objects.get(pk=aid)
            RoomAmenity.objects.get_or_create(room_type=room_type, amenity=amenity)
        except Amenity.DoesNotExist:
            pass

    messages.success(request, f'Đã lưu loại phòng "{room_type.name}".')
    return redirect('dashboard:roomtype_list', hotel_pk=hotel.pk)


# ═══════════════════════════════════════════════════════════
# ROOMS — Phòng thực tế (gắn vào hotel cụ thể)
# ═══════════════════════════════════════════════════════════
@login_required
@staff_required
def room_by_hotel(request, hotel_pk):
    hotel  = get_object_or_404(Hotel, pk=hotel_pk)
    rooms  = Room.objects.filter(hotel=hotel).select_related('room_type').order_by('floor', 'room_number')
    status_counts = {
        'available':   rooms.filter(status='available').count(),
        'occupied':    rooms.filter(status='occupied').count(),
        'maintenance': rooms.filter(status='maintenance').count(),
    }
    return render(request, 'dashboard/rooms/room_list.html', {
        'hotel': hotel, 'rooms': rooms,
        'status_counts': status_counts,
        'status_choices': Room.STATUS_CHOICES,
        'page': 'rooms',
    })


@login_required
@staff_required
def room_create(request, hotel_pk):
    hotel      = get_object_or_404(Hotel, pk=hotel_pk)
    room_types = hotel.room_types.filter(is_active=True)
    if request.method == 'POST':
        return _save_room(request, hotel, None)
    return render(request, 'dashboard/rooms/room_form.html', {
        'hotel': hotel, 'room_types': room_types,
        'status_choices': Room.STATUS_CHOICES,
        'page': 'rooms', 'action': 'Thêm phòng',
    })


@login_required
@staff_required
def room_edit(request, hotel_pk, pk):
    hotel = get_object_or_404(Hotel, pk=hotel_pk)
    room  = get_object_or_404(Room, pk=pk, hotel=hotel)
    room_types = hotel.room_types.filter(is_active=True)
    if request.method == 'POST':
        return _save_room(request, hotel, room)
    return render(request, 'dashboard/rooms/room_form.html', {
        'hotel': hotel, 'room': room, 'room_types': room_types,
        'status_choices': Room.STATUS_CHOICES,
        'page': 'rooms', 'action': 'Sửa phòng',
    })


@login_required
@staff_required
def room_delete(request, hotel_pk, pk):
    hotel = get_object_or_404(Hotel, pk=hotel_pk)
    room  = get_object_or_404(Room, pk=pk, hotel=hotel)
    if request.method == 'POST':
        num = room.room_number
        room.delete()
        messages.success(request, f'Đã xóa phòng {num}.')
    return redirect('dashboard:room_by_hotel', hotel_pk=hotel_pk)


@login_required
@staff_required
def room_bulk_create(request, hotel_pk):
    """Tạo hàng loạt phòng theo tầng."""
    hotel      = get_object_or_404(Hotel, pk=hotel_pk)
    room_types = hotel.room_types.filter(is_active=True)
    if request.method == 'POST':
        room_type_id = request.POST.get('room_type_id')
        floor_start  = int(request.POST.get('floor_start', 1))
        floor_end    = int(request.POST.get('floor_end', 1))
        rooms_per_floor = int(request.POST.get('rooms_per_floor', 10))
        status       = request.POST.get('status', 'available')

        try:
            room_type = RoomType.objects.get(pk=room_type_id, hotel=hotel)
        except RoomType.DoesNotExist:
            messages.error(request, 'Loại phòng không hợp lệ.')
            return redirect('dashboard:room_by_hotel', hotel_pk=hotel_pk)

        created, skipped = 0, 0
        for floor in range(floor_start, floor_end + 1):
            for i in range(1, rooms_per_floor + 1):
                room_number = f'{floor}{i:02d}'
                _, ok = Room.objects.get_or_create(
                    hotel=hotel, room_number=room_number,
                    defaults={'room_type': room_type, 'floor': floor, 'status': status}
                )
                if ok: created += 1
                else:  skipped += 1

        messages.success(request, f'✅ Đã tạo {created} phòng. Bỏ qua {skipped} phòng đã tồn tại.')
        return redirect('dashboard:room_by_hotel', hotel_pk=hotel_pk)

    return render(request, 'dashboard/rooms/room_bulk.html', {
        'hotel': hotel, 'room_types': room_types,
        'status_choices': Room.STATUS_CHOICES,
        'page': 'rooms',
    })


def _save_room(request, hotel, room):
    data = request.POST
    room_type_id = data.get('room_type_id')
    room_number  = data.get('room_number', '').strip()

    if not room_number:
        messages.error(request, 'Số phòng không được để trống.')
        return redirect('dashboard:room_by_hotel', hotel_pk=hotel.pk)

    try:
        room_type = RoomType.objects.get(pk=room_type_id, hotel=hotel)
    except RoomType.DoesNotExist:
        messages.error(request, 'Loại phòng không hợp lệ.')
        return redirect('dashboard:room_by_hotel', hotel_pk=hotel.pk)

    floor_val = data.get('floor', '').strip()
    floor     = int(floor_val) if floor_val.isdigit() else None

    if room:
        room.room_type   = room_type
        room.room_number = room_number
        room.floor       = floor
        room.status      = data.get('status', 'available')
        room.note        = data.get('note', '').strip()
        try:
            room.save()
            messages.success(request, f'Đã cập nhật phòng {room_number}.')
        except Exception:
            messages.error(request, f'Số phòng {room_number} đã tồn tại trong khách sạn này.')
    else:
        try:
            Room.objects.create(
                hotel      = hotel,
                room_type  = room_type,
                room_number= room_number,
                floor      = floor,
                status     = data.get('status', 'available'),
                note       = data.get('note', '').strip(),
            )
            messages.success(request, f'Đã thêm phòng {room_number}.')
        except Exception:
            messages.error(request, f'Số phòng {room_number} đã tồn tại trong khách sạn này.')

    return redirect('dashboard:room_by_hotel', hotel_pk=hotel.pk)


# ═══════════════════════════════════════════════════════════
# API — cho chart JS
# ═══════════════════════════════════════════════════════════
@login_required
@staff_required
def api_stats(request):
    today = date.today()
    data = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        data.append({
            'date':     d.strftime('%d/%m'),
            'bookings': Booking.objects.filter(created_at__date=d).count(),
            'revenue':  float(
                Payment.objects.filter(status='paid', paid_at__date=d)
                .aggregate(t=Sum('amount'))['t'] or 0
            ),
        })
    return JsonResponse({'data': data})