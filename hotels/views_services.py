"""
hotels/views_services.py
Thêm vào hotels/views.py hoặc import vào hotels/urls.py
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
import json

from .models import Hotel, Room, HotelService, ServiceRequest


# ─── Guest: Trang gọi dịch vụ trong phòng ────────────────────────────────────

def room_service_portal(request, hotel_slug, room_number):
    """
    Trang portal cho khách đang ở phòng gọi dịch vụ.
    URL: /hotels/<hotel_slug>/room/<room_number>/services/
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
    room  = get_object_or_404(Room, hotel=hotel, room_number=room_number, status='occupied')

    # Lấy tất cả dịch vụ của khách sạn nhóm theo category
    services = HotelService.objects.filter(
        hotel=hotel, is_available=True
    ).order_by('category', 'order', 'name')

    # Nhóm theo category
    from itertools import groupby
    CATEGORY_LABELS = dict(HotelService.CATEGORY_CHOICES)
    grouped = {}
    for s in services:
        cat = s.category
        if cat not in grouped:
            grouped[cat] = {
                'label': CATEGORY_LABELS.get(cat, cat),
                'items': []
            }
        grouped[cat]['items'].append(s)

    # Lịch sử yêu cầu của phòng hôm nay
    recent_requests = ServiceRequest.objects.filter(
        room=room
    ).select_related('service').order_by('-created_at')[:10]

    context = {
        'hotel':           hotel,
        'room':            room,
        'grouped_services': grouped,
        'recent_requests': recent_requests,
    }
    return render(request, 'hotels/room_service_portal.html', context)


# ─── API: Gửi yêu cầu dịch vụ ───────────────────────────────────────────────

@require_POST
def submit_service_request(request, hotel_slug, room_number):
    """
    API endpoint nhận yêu cầu dịch vụ từ khách.
    Trả JSON cho frontend cập nhật live.
    POST /hotels/<hotel_slug>/room/<room_number>/services/request/
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
    room  = get_object_or_404(Room, hotel=hotel, room_number=room_number, status='occupied')

    try:
        data       = json.loads(request.body)
        service_id = data.get('service_id')
        note       = data.get('note', '').strip()
        quantity   = int(data.get('quantity', 1))
        guest_name = data.get('guest_name', '').strip()
        priority   = data.get('priority', 'normal')

        service = get_object_or_404(HotelService, id=service_id, hotel=hotel, is_available=True)

        req = ServiceRequest.objects.create(
            room       = room,
            service    = service,
            guest      = request.user if request.user.is_authenticated else None,
            guest_name = guest_name,
            note       = note,
            quantity   = max(1, min(quantity, 20)),
            priority   = priority if priority in ('normal', 'urgent') else 'normal',
            status     = 'pending',
        )

        eta_text = f'{service.eta_minutes} phút' if service.eta_minutes else 'Sẽ liên hệ sớm'

        return JsonResponse({
            'success':    True,
            'request_id': req.pk,
            'message':    f'✅ Yêu cầu #{req.pk} đã được gửi! ETA: {eta_text}',
            'status':     req.status,
            'service':    service.name,
            'eta':        eta_text,
            'created_at': req.created_at.strftime('%H:%M'),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ─── API: Kiểm tra trạng thái yêu cầu (polling) ─────────────────────────────

def check_request_status(request, request_id):
    """
    Khách poll trạng thái yêu cầu.
    GET /hotels/service-request/<id>/status/
    """
    req = get_object_or_404(ServiceRequest, pk=request_id)
    STATUS_MAP = dict(ServiceRequest.STATUS_CHOICES)
    return JsonResponse({
        'id':         req.pk,
        'status':     req.status,
        'status_display': STATUS_MAP.get(req.status, req.status),
        'staff_note': req.staff_note,
        'updated_at': req.updated_at.strftime('%H:%M:%S'),
    })


# ─── Staff: API cập nhật trạng thái (nhân viên dùng) ────────────────────────
# Trang nhân viên sẽ có chat/dashboard riêng — đây chỉ là API endpoint

@require_POST
def staff_update_request(request, request_id):
    """
    Nhân viên cập nhật trạng thái yêu cầu.
    Cần quyền staff hoặc superuser.
    POST /hotels/service-request/<id>/update/
    """
    if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

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
        if new_status == 'done':
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