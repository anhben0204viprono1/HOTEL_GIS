"""
bookings/views.py — bao gồm flow đặt phòng + thanh toán MoMo
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
import json

from hotels.models import RoomType, Room
from .models import Booking, Payment
from .forms import BookingForm
from . import momo as momo_service


# ══════════════════════════════════════════════════════════════════════════════
# 1. TẠO ĐẶT PHÒNG
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def create_booking(request, room_type_id):
    """Chọn ngày + xác nhận → tạo Booking ở trạng thái pending, rồi → trang thanh toán."""
    room_type = get_object_or_404(RoomType, id=room_type_id, is_active=True)
    hotel     = room_type.hotel
    form      = BookingForm(request.POST or None, room_type=room_type)

    if request.method == 'POST' and form.is_valid():
        check_in   = form.cleaned_data['check_in']
        check_out  = form.cleaned_data['check_out']
        num_guests = form.cleaned_data['num_guests']
        note       = form.cleaned_data['note']

        # Tìm phòng còn trống chưa bị đặt chồng ngày
        booked_ids = Booking.objects.filter(
            room__room_type=room_type,
            status__in=['pending', 'confirmed', 'checked_in'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).values_list('room_id', flat=True)

        available_room = Room.objects.filter(
            room_type=room_type, status='available',
        ).exclude(id__in=booked_ids).first()

        if not available_room:
            messages.error(request,
                '😔 Không còn phòng trống trong khoảng thời gian này. Vui lòng thử ngày khác.')
            return render(request, 'bookings/create.html', {
                'form': form, 'room_type': room_type, 'hotel': hotel,
                'available_count': 0,
            })

        with transaction.atomic():
            nights      = (check_out - check_in).days
            total_price = room_type.price_per_night * nights
            booking = Booking.objects.create(
                user=request.user, room=available_room,
                check_in=check_in, check_out=check_out,
                num_guests=num_guests, note=note,
                total_price=total_price, status='pending',
            )

        # Chuyển sang trang thanh toán
        return redirect('bookings:payment', pk=booking.pk)

    available_count = Room.objects.filter(
        room_type=room_type, status='available'
    ).count()

    return render(request, 'bookings/create.html', {
        'form': form, 'room_type': room_type,
        'hotel': hotel, 'available_count': available_count,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 2. TRANG THANH TOÁN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def payment_page(request, pk):
    """Hiển thị trang chọn phương thức thanh toán."""
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel', 'user'),
        pk=pk, user=request.user,
    )

    # Nếu booking đã được xử lý rồi, chuyển thẳng đến trang chi tiết
    if booking.status not in ('pending',):
        return redirect('bookings:detail', pk=pk)

    # Kiểm tra xem đã có payment thành công chưa
    paid = booking.payments.filter(status='paid').exists()
    if paid:
        return redirect('bookings:payment_result', pk=pk)

    return render(request, 'bookings/payment.html', {'booking': booking})


# ══════════════════════════════════════════════════════════════════════════════
# 3. KHỞI TẠO THANH TOÁN MOMO
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def initiate_momo(request, pk):
    """Gọi API MoMo → trả về pay_url để redirect."""
    if request.method != 'POST':
        return redirect('bookings:payment', pk=pk)

    booking = get_object_or_404(Booking, pk=pk, user=request.user, status='pending')

    # Tạo URL callback
    return_url = request.build_absolute_uri(
        reverse('bookings:momo_return', kwargs={'pk': pk})
    )
    ipn_url = request.build_absolute_uri(
        reverse('bookings:momo_ipn', kwargs={'pk': pk})
    )

    result = momo_service.create_payment(booking, return_url, ipn_url)

    if result['ok']:
        # Lưu payment ở trạng thái pending
        Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            method='momo',
            status='pending',
            transaction_code=result.get('order_id', ''),
            note=f"requestId: {result.get('request_id', '')}",
        )
        return redirect(result['pay_url'])

    # Lỗi kết nối MoMo
    messages.error(request, f"❌ Không thể kết nối MoMo: {result['message']}")
    return redirect('bookings:payment', pk=pk)


# ══════════════════════════════════════════════════════════════════════════════
# 4. THANH TOÁN TIỀN MẶT / CHUYỂN KHOẢN (tại quầy)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def pay_at_counter(request, pk):
    """Chọn thanh toán tại quầy — tạo Payment pending, confirm booking."""
    if request.method != 'POST':
        return redirect('bookings:payment', pk=pk)

    method  = request.POST.get('method', 'cash')  # cash | bank_transfer
    booking = get_object_or_404(Booking, pk=pk, user=request.user, status='pending')

    with transaction.atomic():
        Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            method=method,
            status='pending',
            note='Thanh toán tại quầy — chờ xác nhận từ nhân viên',
        )
        booking.status = 'confirmed'
        booking.save()

    messages.success(request,
        f'🎉 Đặt phòng #{booking.id} đã được xác nhận! '
        'Vui lòng thanh toán tại quầy lễ tân khi nhận phòng.')
    return redirect('bookings:detail', pk=pk)


# ══════════════════════════════════════════════════════════════════════════════
# 5. MOMO IPN (Instant Payment Notification) — gọi từ server MoMo
# ══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
def momo_ipn(request, pk):
    """MoMo gọi về để xác nhận kết quả thanh toán (server-to-server)."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse(status=400)

    # Xác thực chữ ký
    if not momo_service.verify_ipn(data):
        return HttpResponse(status=403)

    booking = get_object_or_404(Booking, pk=pk)
    result_code = int(data.get('resultCode', -1))
    trans_id    = str(data.get('transId', ''))
    order_id    = data.get('orderId', '')

    with transaction.atomic():
        payment = booking.payments.filter(
            transaction_code=order_id, method='momo'
        ).first()

        if payment:
            if result_code == 0:
                payment.status = 'paid'
                payment.transaction_code = order_id
                payment.note = f'transId MoMo: {trans_id}'
                payment.paid_at = timezone.now()
                payment.save()

                if booking.status == 'pending':
                    booking.status = 'confirmed'
                    booking.save()
            else:
                payment.status = 'failed'
                payment.note = f'resultCode: {result_code} — {data.get("message", "")}'
                payment.save()

    return HttpResponse('{"status": "ok"}', content_type='application/json')


# ══════════════════════════════════════════════════════════════════════════════
# 6. MOMO RETURN URL — redirect người dùng sau khi thanh toán
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def momo_return(request, pk):
    """MoMo redirect người dùng về đây sau khi hoàn tất (thành công hoặc thất bại)."""
    booking     = get_object_or_404(Booking, pk=pk, user=request.user)
    result_code = int(request.GET.get('resultCode', -1))
    order_id    = request.GET.get('orderId', '')
    trans_id    = request.GET.get('transId', '')
    message     = request.GET.get('message', '')

    with transaction.atomic():
        payment = booking.payments.filter(
            transaction_code=order_id, method='momo'
        ).first()

        # Cập nhật nếu IPN chưa gọi về kịp
        if payment and payment.status == 'pending':
            if result_code == 0:
                payment.status = 'paid'
                payment.note = f'transId MoMo: {trans_id}'
                payment.paid_at = timezone.now()
                payment.save()
                if booking.status == 'pending':
                    booking.status = 'confirmed'
                    booking.save()
            else:
                payment.status = 'failed'
                payment.note = f'resultCode: {result_code} — {message}'
                payment.save()

    return redirect('bookings:payment_result', pk=pk)


# ══════════════════════════════════════════════════════════════════════════════
# 7. TRANG KẾT QUẢ THANH TOÁN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def payment_result(request, pk):
    """Hiển thị trang kết quả thanh toán."""
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel'),
        pk=pk, user=request.user,
    )
    last_payment = booking.payments.order_by('-created_at').first()
    success = last_payment and last_payment.status == 'paid'

    return render(request, 'bookings/payment_result.html', {
        'booking':      booking,
        'last_payment': last_payment,
        'success':      success,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 8. CHI TIẾT & HỦY (giữ nguyên)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel', 'user'),
        pk=pk, user=request.user,
    )
    return render(request, 'bookings/detail.html', {'booking': booking})


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        if booking.can_cancel():
            booking.status       = 'cancelled'
            booking.cancelled_at = timezone.now()
            booking.cancel_reason = request.POST.get('reason', '').strip()
            booking.save()
            messages.warning(request, f'Đặt phòng #{booking.id} đã được hủy.')
        else:
            messages.error(request, 'Không thể hủy đặt phòng ở trạng thái này.')
    return redirect('accounts:profile')