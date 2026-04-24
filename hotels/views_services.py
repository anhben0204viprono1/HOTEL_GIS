"""
hotels/views_services.py
Views xử lý trang gọi dịch vụ của khách đang ở phòng.
"""
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from .models import Hotel, Room, HotelService, ServiceRequest


# ─── Guest: Trang gọi dịch vụ trong phòng ────────────────────────────────────

def room_service_portal(request, hotel_slug, room_number):
    """
    Trang portal cho khách đang ở phòng gọi dịch vụ.
    URL: /<hotel_slug>/room/<room_number>/services/

    FIX: Bỏ filter status='occupied' khỏi get_object_or_404 — nếu phòng
    chưa được set 'occupied' thì trả 404 ngay cả khi URL đúng.
    Thay vào đó: lấy phòng trước, kiểm tra status sau, trả trang lỗi thân thiện.
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)

    # FIX: Chỉ lookup theo hotel + room_number, không filter status ở đây
    room = get_object_or_404(Room, hotel=hotel, room_number=room_number)

    # Nếu phòng không phải 'occupied' → hiện trang thông báo thay vì 404
    if room.status != 'occupied':
        return render(request, 'hotels/room_service_portal.html', {
            'hotel':       hotel,
            'room':        room,
            'unavailable': True,
            'status':      room.get_status_display(),
        })

    services = HotelService.objects.filter(
        hotel=hotel, is_available=True
    ).order_by('category', 'order', 'name')

    # Nhóm theo category
    CATEGORY_LABELS = dict(HotelService.CATEGORY_CHOICES)
    grouped = {}
    for s in services:
        cat = s.category
        if cat not in grouped:
            grouped[cat] = {
                'label': CATEGORY_LABELS.get(cat, cat),
                'items': [],
            }
        grouped[cat]['items'].append(s)

    # Lịch sử yêu cầu của phòng (10 gần nhất)
    recent_requests = ServiceRequest.objects.filter(
        room=room
    ).select_related('service').order_by('-created_at')[:10]

    context = {
        'hotel':            hotel,
        'room':             room,
        'grouped_services': grouped,
        'recent_requests':  recent_requests,
        'unavailable':      False,
    }
    return render(request, 'hotels/room_service_portal.html', context)


# ─── API: Gửi yêu cầu dịch vụ ───────────────────────────────────────────────

@require_POST
def submit_service_request(request, hotel_slug, room_number):
    """
    API endpoint nhận yêu cầu dịch vụ từ khách.
    Trả JSON để frontend cập nhật live.
    POST /<hotel_slug>/room/<room_number>/services/request/
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)

    # FIX: Tương tự — lookup phòng trước, kiểm tra status sau
    room = get_object_or_404(Room, hotel=hotel, room_number=room_number)

    if room.status != 'occupied':
        return JsonResponse(
            {'success': False, 'error': 'Phòng hiện không ở trạng thái có khách.'},
            status=400
        )

    try:
        data       = json.loads(request.body)
        service_id = data.get('service_id')
        note       = data.get('note', '').strip()
        quantity   = int(data.get('quantity', 1))
        guest_name = data.get('guest_name', '').strip()
        priority   = data.get('priority', 'normal')

        service = get_object_or_404(HotelService, id=service_id, hotel=hotel, is_available=True)

        # Validate priority — chỉ chấp nhận giá trị hợp lệ
        valid_priorities = [p[0] for p in ServiceRequest.PRIORITY_CHOICES]
        if priority not in valid_priorities:
            priority = 'normal'

        req = ServiceRequest.objects.create(
            room       = room,
            service    = service,
            guest      = request.user if request.user.is_authenticated else None,
            guest_name = guest_name,
            note       = note,
            quantity   = max(1, min(quantity, 20)),
            priority   = priority,
            status     = 'pending',
        )

        eta_text = f'{service.eta_minutes} phút' if service.eta_minutes else 'Sẽ liên hệ sớm'

        return JsonResponse({
            'success':    True,
            'request_id': req.pk,
            'message':    f'Yêu cầu #{req.pk} đã được gửi! ETA: {eta_text}',
            'status':     req.status,
            'service':    service.name,
            'eta':        eta_text,
            'created_at': req.created_at.strftime('%H:%M'),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ─── API: Kiểm tra trạng thái yêu cầu (polling từ client) ──────────────────

def check_request_status(request, request_id):
    """
    Khách poll trạng thái yêu cầu.
    GET /service-request/<id>/status/
    """
    req = get_object_or_404(ServiceRequest, pk=request_id)
    STATUS_MAP = dict(ServiceRequest.STATUS_CHOICES)
    return JsonResponse({
        'id':             req.pk,
        'status':         req.status,
        'status_display': STATUS_MAP.get(req.status, req.status),
        'staff_note':     req.staff_note,
        'updated_at':     req.updated_at.strftime('%H:%M:%S'),
    })


# ─── API: Nhân viên cập nhật trạng thái ─────────────────────────────────────

@require_POST
def staff_update_request(request, request_id):
    """
    Nhân viên cập nhật trạng thái yêu cầu.
    POST /service-request/<id>/update/

    Cho phép:
      - Django staff/superuser (is_staff=True)
      - Nhân viên có StaffProfile hợp lệ (is_active=True)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Kiểm tra quyền: is_staff/superuser HOẶC có StaffProfile active
    is_authorized = request.user.is_staff or request.user.is_superuser
    if not is_authorized:
        try:
            profile = request.user.staff_profile
            is_authorized = profile.is_active
        except Exception:
            is_authorized = False

    if not is_authorized:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    req = get_object_or_404(ServiceRequest, pk=request_id)
    try:
        data       = json.loads(request.body)
        new_status = data.get('status')
        staff_note = data.get('staff_note', '').strip()

        valid_statuses = [s[0] for s in ServiceRequest.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        req.status     = new_status
        req.staff_note = staff_note

        if new_status == 'accepted' and not req.assigned_to:
            req.assigned_to = request.user

        if new_status == 'done' and not req.done_at:
            req.done_at = timezone.now()

        req.save()

        return JsonResponse({
            'success':    True,
            'request_id': req.pk,
            'status':     req.status,
            'updated_at': req.updated_at.strftime('%H:%M:%S'),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
