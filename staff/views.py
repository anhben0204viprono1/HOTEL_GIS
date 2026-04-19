"""
staff/views.py

Dashboard dành cho nhân viên khách sạn.
- Nhân viên chỉ thấy dữ liệu của khách sạn mình phụ trách.
- Quyền: đăng nhập + có StaffProfile (is_staff KHÔNG cần thiết).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta

from hotels.models import Hotel, Room, RoomType
from bookings.models import Booking, Payment
from .models import StaffProfile


# ── Guard helper ──────────────────────────────────────────────────────────────

def get_staff_profile(user):
    """Trả về StaffProfile nếu user là nhân viên, ngược lại None."""
    try:
        return user.staff_profile
    except StaffProfile.DoesNotExist:
        return None


def staff_login_required(view_func):
    """Decorator: yêu cầu đăng nhập VÀ có StaffProfile."""
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL + f'?next={request.path}')
        profile = get_staff_profile(request.user)
        if not profile:
            messages.error(request, '⛔ Bạn không có quyền truy cập trang nhân viên.')
            return redirect('/')
        if not profile.is_active:
            messages.error(request, '⛔ Tài khoản nhân viên của bạn đã bị vô hiệu hóa.')
            return redirect('/')
        request.staff_profile = profile
        return view_func(request, *args, **kwargs)

    return wrapper


# ═══════════════════════════════════════════════════════════
# HOME — Dashboard tổng quan nhân viên
# ═══════════════════════════════════════════════════════════
@staff_login_required
def staff_home(request):
    profile = request.staff_profile
    hotel   = profile.hotel
    today   = date.today()

    # Thống kê phòng
    rooms = Room.objects.filter(hotel=hotel)
    room_stats = {
        'total':       rooms.count(),
        'available':   rooms.filter(status='available').count(),
        'occupied':    rooms.filter(status='occupied').count(),
        'maintenance': rooms.filter(status='maintenance').count(),
    }

    # Booking hôm nay
    booking_today = {
        'checkin':  Booking.objects.filter(
            room__hotel=hotel, check_in=today, status='confirmed'
        ).count(),
        'checkout': Booking.objects.filter(
            room__hotel=hotel, check_out=today, status='checked_in'
        ).count(),
        'pending':  Booking.objects.filter(
            room__hotel=hotel, status='pending'
        ).count(),
    }

    # Yêu cầu dịch vụ chưa xử lý
    pending_requests = ServiceRequest.objects.filter(
        hotel=hotel, status='pending'
    ).order_by('-priority', '-created_at')[:5]

    urgent_count = ServiceRequest.objects.filter(
        hotel=hotel, status__in=['pending', 'in_progress'], priority='urgent'
    ).count()

    # Booking cần check-in / check-out hôm nay
    checkins_today = Booking.objects.filter(
        room__hotel=hotel, check_in=today, status='confirmed'
    ).select_related('user', 'room__room_type')[:8]

    checkouts_today = Booking.objects.filter(
        room__hotel=hotel, check_out=today, status='checked_in'
    ).select_related('user', 'room__room_type')[:8]

    # Booking mới nhất của khách sạn
    recent_bookings = Booking.objects.filter(
        room__hotel=hotel
    ).select_related('user', 'room__room_type').order_by('-created_at')[:6]

    context = {
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
    }
    return render(request, 'staff/home.html', context)


# ═══════════════════════════════════════════════════════════
# ROOMS — Quản lý phòng (chỉ khách sạn của nhân viên)
# ═══════════════════════════════════════════════════════════
@staff_login_required
def staff_rooms(request):
    profile = request.staff_profile
    hotel   = profile.hotel

    status_filter = request.GET.get('status', '')
    floor_filter  = request.GET.get('floor', '')

    rooms = Room.objects.filter(hotel=hotel).select_related('room_type').order_by('floor', 'room_number')

    if status_filter:
        rooms = rooms.filter(status=status_filter)
    if floor_filter:
        rooms = rooms.filter(floor=floor_filter)

    floors = Room.objects.filter(hotel=hotel).values_list('floor', flat=True).distinct().order_by('floor')

    status_counts = {
        'available':   Room.objects.filter(hotel=hotel, status='available').count(),
        'occupied':    Room.objects.filter(hotel=hotel, status='occupied').count(),
        'maintenance': Room.objects.filter(hotel=hotel, status='maintenance').count(),
    }

    context = {
        'profile':        profile,
        'hotel':          hotel,
        'rooms':          rooms,
        'floors':         floors,
        'status_counts':  status_counts,
        'status_choices': Room.STATUS_CHOICES,
        'filters': {'status': status_filter, 'floor': floor_filter},
        'page':           'rooms',
    }
    return render(request, 'staff/rooms.html', context)


@staff_login_required
def staff_room_update_status(request, pk):
    """Cập nhật trạng thái phòng — chỉ phòng thuộc khách sạn của nhân viên."""
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
            messages.success(request, f'✅ Đã cập nhật phòng {room.room_number} → {room.get_status_display()}')
        else:
            messages.error(request, 'Trạng thái không hợp lệ.')

    return redirect('staff:rooms')


# ═══════════════════════════════════════════════════════════
# BOOKINGS — Xem booking của khách sạn mình
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
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(room__room_number__icontains=q)
        )

    context = {
        'profile':        profile,
        'hotel':          hotel,
        'bookings':       bookings,
        'status_choices': Booking.STATUS_CHOICES,
        'filters': {'status': status_filter, 'date': date_filter, 'q': q},
        'page':           'bookings',
    }
    return render(request, 'staff/bookings.html', context)


@staff_login_required
def staff_booking_detail(request, pk):
    profile = request.staff_profile
    booking = get_object_or_404(Booking, pk=pk, room__hotel=profile.hotel)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        try:
            booking.apply_status_change(new_status)
            messages.success(request, f'✅ Đã cập nhật trạng thái: {booking.get_status_display()}')
        except Exception as e:
            messages.error(request, str(e))
        return redirect('staff:booking_detail', pk=pk)

    context = {
        'profile': profile,
        'hotel':   profile.hotel,
        'booking': booking,
        'page':    'bookings',
    }
    return render(request, 'staff/booking_detail.html', context)


# ═══════════════════════════════════════════════════════════
# SERVICE REQUESTS — Yêu cầu dịch vụ
# ═══════════════════════════════════════════════════════════
@staff_login_required
def staff_service_requests(request):
    profile = request.staff_profile
    hotel   = profile.hotel

    status_filter   = request.GET.get('status', '')
    type_filter     = request.GET.get('type', '')
    priority_filter = request.GET.get('priority', '')

    requests_qs = ServiceRequest.objects.filter(
        hotel=hotel
    ).select_related('guest', 'room', 'assigned_to__user').order_by('-created_at')

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    if type_filter:
        requests_qs = requests_qs.filter(request_type=type_filter)
    if priority_filter:
        requests_qs = requests_qs.filter(priority=priority_filter)

    # Thống kê nhanh
    counts = {
        'pending':     ServiceRequest.objects.filter(hotel=hotel, status='pending').count(),
        'in_progress': ServiceRequest.objects.filter(hotel=hotel, status='in_progress').count(),
        'resolved':    ServiceRequest.objects.filter(hotel=hotel, status='resolved').count(),
        'urgent':      ServiceRequest.objects.filter(hotel=hotel, priority='urgent', status__in=['pending','in_progress']).count(),
    }

    # Danh sách nhân viên để assign
    staff_list = StaffProfile.objects.filter(hotel=hotel, is_active=True).select_related('user')

    context = {
        'profile':         profile,
        'hotel':           hotel,
        'requests':        requests_qs,
        'counts':          counts,
        'staff_list':      staff_list,
        'status_choices':  ServiceRequest.STATUS_CHOICES,
        'type_choices':    ServiceRequest.TYPE_CHOICES,
        'priority_choices':ServiceRequest.PRIORITY_CHOICES,
        'filters': {
            'status': status_filter,
            'type': type_filter,
            'priority': priority_filter,
        },
        'page': 'requests',
    }
    return render(request, 'staff/service_requests.html', context)


@staff_login_required
def staff_service_request_update(request, pk):
    """Cập nhật trạng thái / ghi chú / giao việc cho một yêu cầu dịch vụ."""
    profile = request.staff_profile
    req     = get_object_or_404(ServiceRequest, pk=pk, hotel=profile.hotel)

    if request.method == 'POST':
        new_status  = request.POST.get('status', req.status)
        staff_note  = request.POST.get('staff_note', '').strip()
        assigned_id = request.POST.get('assigned_to', '')

        req.status     = new_status
        req.staff_note = staff_note

        if assigned_id:
            try:
                assigned = StaffProfile.objects.get(pk=assigned_id, hotel=profile.hotel)
                req.assigned_to = assigned
            except StaffProfile.DoesNotExist:
                pass

        if new_status == 'resolved' and not req.resolved_at:
            req.resolved_at = timezone.now()

        req.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': True,
                'status': new_status,
                'display': req.get_status_display(),
            })

        messages.success(request, f'✅ Đã cập nhật yêu cầu #{req.id}')
        return redirect('staff:service_requests')

    return redirect('staff:service_requests')


@staff_login_required
def staff_service_request_create(request):
    """Nhân viên tạo yêu cầu dịch vụ thay cho khách (walk-in)."""
    profile = request.staff_profile
    hotel   = profile.hotel

    if request.method == 'POST':
        room_id = request.POST.get('room')
        title   = request.POST.get('title', '').strip()

        if not title:
            messages.error(request, 'Tiêu đề yêu cầu không được để trống.')
            return redirect('staff:service_requests')

        room = None
        if room_id:
            try:
                room = Room.objects.get(pk=room_id, hotel=hotel)
            except Room.DoesNotExist:
                pass

        ServiceRequest.objects.create(
            hotel        = hotel,
            room         = room,
            request_type = request.POST.get('request_type', 'other'),
            title        = title,
            description  = request.POST.get('description', '').strip(),
            priority     = request.POST.get('priority', 'medium'),
            assigned_to  = profile,
        )
        messages.success(request, f'✅ Đã tạo yêu cầu: {title}')
        return redirect('staff:service_requests')

    return redirect('staff:service_requests')


# ═══════════════════════════════════════════════════════════
# API — số liệu nhanh cho dashboard
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
