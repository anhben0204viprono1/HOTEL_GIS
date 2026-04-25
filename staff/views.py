"""
staff/views.py
Tất cả status ServiceRequest khớp với model:
  pending | accepted | processing | done | cancelled
Priority: normal | urgent  (không có 'medium')
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta

from hotels.models import Hotel, Room, RoomType, ServiceRequest, HotelService
from bookings.models import Booking
from .models import StaffProfile


# ── Guard ─────────────────────────────────────────────────────────────────────

def get_staff_profile(user):
    try:
        return user.staff_profile
    except StaffProfile.DoesNotExist:
        return None


def staff_login_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL + f'?next={request.path}')
        profile = get_staff_profile(request.user)
        if not profile:
            messages.error(request, 'Bạn không có quyền truy cập trang nhân viên.')
            return redirect('/')
        if not profile.is_active:
            messages.error(request, 'Tài khoản nhân viên của bạn đã bị vô hiệu hóa.')
            return redirect('/')
        request.staff_profile = profile
        return view_func(request, *args, **kwargs)

    return wrapper


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hotel_rooms(hotel):
    return Room.objects.filter(hotel=hotel)


def _sreq_qs(hotel):
    """ServiceRequest lọc qua room__hotel (không có FK hotel trực tiếp)."""
    return ServiceRequest.objects.filter(room__hotel=hotel)


def _sreq_count(hotel, **kwargs):
    return _sreq_qs(hotel).filter(**kwargs).count()


# ═══════════════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════════════
@staff_login_required
def staff_home(request):
    profile = request.staff_profile
    hotel   = profile.hotel
    today   = date.today()

    rooms = _hotel_rooms(hotel)
    room_stats = {
        'total':       rooms.count(),
        'available':   rooms.filter(status='available').count(),
        'occupied':    rooms.filter(status='occupied').count(),
        'maintenance': rooms.filter(status='maintenance').count(),
    }

    booking_today = {
        'checkin':  Booking.objects.filter(room__hotel=hotel, check_in=today,  status='confirmed').count(),
        'checkout': Booking.objects.filter(room__hotel=hotel, check_out=today, status='checked_in').count(),
        'pending':  Booking.objects.filter(room__hotel=hotel, status='pending').count(),
    }

    pending_requests = _sreq_qs(hotel).filter(
        status='pending'
    ).select_related('service', 'room').order_by('-priority', '-created_at')[:5]

    # FIX: dùng đúng status theo model (không có 'in_progress')
    urgent_count = _sreq_count(
        hotel,
        status__in=['pending', 'accepted', 'processing'],
        priority='urgent',
    )

    checkins_today = Booking.objects.filter(
        room__hotel=hotel, check_in=today, status='confirmed'
    ).select_related('user', 'room__room_type')[:8]

    checkouts_today = Booking.objects.filter(
        room__hotel=hotel, check_out=today, status='checked_in'
    ).select_related('user', 'room__room_type')[:8]

    recent_bookings = Booking.objects.filter(
        room__hotel=hotel
    ).select_related('user', 'room__room_type').order_by('-created_at')[:6]

    return render(request, 'staff/home.html', {
        'profile':          profile,
        'hotel':            hotel,
        'room_stats':       room_stats,
        'booking_today':    booking_today,
        'pending_requests': pending_requests,
        'urgent_count':     urgent_count,
        'checkins_today':   checkins_today,
        'checkouts_today':  checkouts_today,
        'recent_bookings':  recent_bookings,
        'today':            today,
        'page':             'home',
    })


# ═══════════════════════════════════════════════════════════
# ROOMS
# ═══════════════════════════════════════════════════════════
@staff_login_required
def staff_rooms(request):
    profile = request.staff_profile
    hotel   = profile.hotel

    status_filter = request.GET.get('status', '')
    floor_filter  = request.GET.get('floor', '')

    rooms = _hotel_rooms(hotel).select_related('room_type').order_by('floor', 'room_number')
    if status_filter:
        rooms = rooms.filter(status=status_filter)
    if floor_filter:
        rooms = rooms.filter(floor=floor_filter)

    floors = _hotel_rooms(hotel).values_list('floor', flat=True).distinct().order_by('floor')

    status_counts = {
        'available':   _hotel_rooms(hotel).filter(status='available').count(),
        'occupied':    _hotel_rooms(hotel).filter(status='occupied').count(),
        'maintenance': _hotel_rooms(hotel).filter(status='maintenance').count(),
    }

    return render(request, 'staff/rooms.html', {
        'profile':        profile,
        'hotel':          hotel,
        'rooms':          rooms,
        'floors':         floors,
        'status_counts':  status_counts,
        'status_choices': Room.STATUS_CHOICES,
        'filters':        {'status': status_filter, 'floor': floor_filter},
        'page':           'rooms',
    })


@staff_login_required
def staff_room_update_status(request, pk):
    profile = request.staff_profile
    room    = get_object_or_404(Room, pk=pk, hotel=profile.hotel)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid = [s[0] for s in Room.STATUS_CHOICES]
        if new_status in valid:
            room.status = new_status
            room.note   = request.POST.get('note', room.note)
            room.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'status': new_status, 'display': room.get_status_display()})
            messages.success(request, f'Đã cập nhật phòng {room.room_number} → {room.get_status_display()}')
        else:
            messages.error(request, 'Trạng thái không hợp lệ.')

    return redirect('staff:rooms')


# ═══════════════════════════════════════════════════════════
# BOOKINGS
# ═══════════════════════════════════════════════════════════
@staff_login_required
def staff_bookings(request):
    profile = request.staff_profile
    hotel   = profile.hotel

    status_filter = request.GET.get('status', '')
    date_filter   = request.GET.get('date', '')
    q             = request.GET.get('q', '')

    bookings = Booking.objects.filter(
        room__hotel=hotel
    ).select_related('user', 'room__room_type').order_by('-created_at')

    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if date_filter:
        bookings = bookings.filter(check_in=date_filter)
    if q:
        bookings = bookings.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)  |
            Q(user__email__icontains=q)      |
            Q(room__room_number__icontains=q)
        )

    return render(request, 'staff/bookings.html', {
        'profile':        profile,
        'hotel':          hotel,
        'bookings':       bookings,
        'status_choices': Booking.STATUS_CHOICES,
        'filters':        {'status': status_filter, 'date': date_filter, 'q': q},
        'page':           'bookings',
    })


@staff_login_required
def staff_booking_detail(request, pk):
    profile = request.staff_profile
    booking = get_object_or_404(Booking, pk=pk, room__hotel=profile.hotel)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        try:
            booking.apply_status_change(new_status)
            messages.success(request, f'Đã cập nhật: {booking.get_status_display()}')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('staff:booking_detail', pk=pk)

    return render(request, 'staff/booking_detail.html', {
        'profile': profile,
        'hotel':   profile.hotel,
        'booking': booking,
        'page':    'bookings',
    })


# ═══════════════════════════════════════════════════════════
# SERVICE REQUESTS
# ═══════════════════════════════════════════════════════════
@staff_login_required   # FIX: bản gốc thiếu decorator này → bất kỳ ai cũng xem được
def staff_service_requests(request):
    profile = request.staff_profile
    hotel   = profile.hotel

    status_filter   = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')

    requests_qs = _sreq_qs(hotel).select_related(
        'guest', 'room', 'service', 'assigned_to'
    ).order_by('-created_at')

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    if priority_filter:
        requests_qs = requests_qs.filter(priority=priority_filter)

    # FIX: dùng đúng status keys từ ServiceRequest.STATUS_CHOICES
    counts = {
        'pending':    _sreq_count(hotel, status='pending'),
        'accepted':   _sreq_count(hotel, status='accepted'),
        'processing': _sreq_count(hotel, status='processing'),
        'done':       _sreq_count(hotel, status='done'),
        'urgent':     _sreq_count(hotel, priority='urgent', status__in=['pending', 'accepted', 'processing']),
    }

    staff_list = StaffProfile.objects.filter(
        hotel=hotel, is_active=True
    ).select_related('user')

    services = HotelService.objects.filter(
        hotel=hotel, is_available=True
    ).order_by('order', 'name')

    hotel_rooms = _hotel_rooms(hotel).order_by('floor', 'room_number')

    return render(request, 'staff/service_requests.html', {
        'profile':          profile,
        'hotel':            hotel,
        'requests':         requests_qs,
        'counts':           counts,
        'staff_list':       staff_list,
        'services':         services,
        'hotel_rooms':      hotel_rooms,
        'status_choices':   ServiceRequest.STATUS_CHOICES,
        'priority_choices': ServiceRequest.PRIORITY_CHOICES,
        'filters': {
            'status':   status_filter,
            'priority': priority_filter,
        },
        'page': 'requests',
    })


@staff_login_required
def staff_service_request_update(request, pk):
    profile = request.staff_profile
    req     = get_object_or_404(ServiceRequest, pk=pk, room__hotel=profile.hotel)

    if request.method == 'POST':
        new_status = request.POST.get('status', req.status)
        staff_note = request.POST.get('staff_note', '').strip()

        # Validate status
        valid_statuses = [s[0] for s in ServiceRequest.STATUS_CHOICES]
        if new_status not in valid_statuses:
            messages.error(request, 'Trạng thái không hợp lệ.')
            return redirect('staff:service_requests')

        req.status     = new_status
        req.staff_note = staff_note

        # assigned_to là FK tới User
        assigned_id = request.POST.get('assigned_to', '')
        if assigned_id:
            try:
                staff_member    = StaffProfile.objects.get(pk=assigned_id, hotel=profile.hotel)
                req.assigned_to = staff_member.user
            except StaffProfile.DoesNotExist:
                pass

        # FIX: kiểm tra đúng status 'done' (bản gốc check 'resolved' không có trong model)
        if new_status == 'done' and not req.done_at:
            req.done_at = timezone.now()

        req.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok':      True,
                'status':  req.status,
                'display': req.get_status_display(),
            })

        messages.success(request, f'Đã cập nhật yêu cầu #{req.id}')

    return redirect('staff:service_requests')


@staff_login_required
def staff_service_request_create(request):
    profile = request.staff_profile
    hotel   = profile.hotel

    if request.method == 'POST':
        service_id = request.POST.get('service', '').strip()
        room_id    = request.POST.get('room', '').strip()
        note       = request.POST.get('note', '').strip()
        # FIX: default 'normal' thay vì 'medium' (không có trong PRIORITY_CHOICES)
        priority   = request.POST.get('priority', 'normal')
        quantity   = request.POST.get('quantity', '1')

        if not service_id:
            messages.error(request, 'Vui lòng chọn loại dịch vụ.')
            return redirect('staff:service_requests')

        try:
            service = HotelService.objects.get(pk=service_id, hotel=hotel)
        except HotelService.DoesNotExist:
            messages.error(request, 'Dịch vụ không hợp lệ.')
            return redirect('staff:service_requests')

        if not room_id:
            messages.error(request, 'Vui lòng chọn phòng.')
            return redirect('staff:service_requests')

        try:
            room = Room.objects.get(pk=room_id, hotel=hotel)
        except Room.DoesNotExist:
            messages.error(request, 'Phòng không hợp lệ.')
            return redirect('staff:service_requests')

        try:
            quantity = max(1, int(quantity))
        except ValueError:
            quantity = 1

        # Validate priority
        valid_priorities = [p[0] for p in ServiceRequest.PRIORITY_CHOICES]
        if priority not in valid_priorities:
            priority = 'normal'

        ServiceRequest.objects.create(
            room        = room,
            service     = service,
            guest       = request.user,
            note        = note,
            quantity    = quantity,
            priority    = priority,
            status      = 'pending',
            assigned_to = request.user,
            staff_note  = '',
        )

        messages.success(request, f'Đã tạo yêu cầu: {service.name} — Phòng {room.room_number}')

    return redirect('staff:service_requests')


# ═══════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════
@staff_login_required
def staff_api_stats(request):
    profile = request.staff_profile
    hotel   = profile.hotel
    today   = date.today()

    data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        data.append({
            'date':     d.strftime('%d/%m'),
            'bookings': Booking.objects.filter(room__hotel=hotel, created_at__date=d).count(),
            'checkins': Booking.objects.filter(room__hotel=hotel, check_in=d).count(),
        })

    return JsonResponse({'data': data})
