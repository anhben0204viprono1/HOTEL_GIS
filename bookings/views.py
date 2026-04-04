from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from hotels.models import RoomType, Room
from .models import Booking, Payment
from .forms import BookingForm
from .emails import send_booking_confirmation   # ← thêm dòng này
from .services import create_pending_payment_with_qr
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import json
from . import momo


@login_required
def create_booking(request, room_type_id):
    room_type = get_object_or_404(RoomType, id=room_type_id, is_active=True)
    hotel     = room_type.hotel

    form = BookingForm(request.POST or None, room_type=room_type)

    if request.method == 'POST' and form.is_valid():
        check_in   = form.cleaned_data['check_in']
        check_out  = form.cleaned_data['check_out']
        num_guests = form.cleaned_data['num_guests']
        note       = form.cleaned_data['note']

        # Tìm phòng còn trống chưa bị đặt trong khoảng ngày
        booked_room_ids = Booking.objects.filter(
            room__room_type=room_type,
            status__in=['pending', 'confirmed', 'checked_in'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).values_list('room_id', flat=True)

        available_room = Room.objects.filter(
            room_type=room_type,
            status='available',
        ).exclude(id__in=booked_room_ids).first()

        if not available_room:
            messages.error(
                request,
                '😔 Không còn phòng trống cho loại phòng này trong khoảng thời gian đã chọn. '
                'Vui lòng thử ngày khác.'
            )
            return render(request, 'bookings/create.html', {
                'form': form, 'room_type': room_type, 'hotel': hotel
            })

        with transaction.atomic():
            nights      = (check_out - check_in).days
            total_price = room_type.price_per_night * nights

            booking = Booking.objects.create(
                user        = request.user,
                room        = available_room,
                check_in    = check_in,
                check_out   = check_out,
                num_guests  = num_guests,
                note        = note,
                total_price = total_price,
                status      = 'pending',
            )

        messages.success(
            request,
            f'🎉 Tạo đặt phòng thành công! Mã đặt phòng: #{booking.id}. '
            f'Vui lòng thanh toán để hoàn tất.'
        )
        method = 'momo' if getattr(settings, 'MOMO_ENABLED', False) else 'bank_transfer'
        url = reverse('bookings:create_payment', kwargs={'pk': booking.pk})
        return redirect(f'{url}?method={method}')

    available_count = Room.objects.filter(
        room_type=room_type, status='available'
    ).count()

    context = {
        'form':            form,
        'room_type':       room_type,
        'hotel':           hotel,
        'available_count': available_count,
    }
    return render(request, 'bookings/create.html', context)


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel', 'user'),
        pk=pk, user=request.user
    )
    return render(request, 'bookings/detail.html', {'booking': booking})


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        if booking.can_cancel():
            booking.status        = 'cancelled'
            booking.cancelled_at  = timezone.now()
            booking.cancel_reason = request.POST.get('reason', '').strip()
            booking.save()
            messages.warning(request, f'Đặt phòng #{booking.id} đã được hủy.')
        else:
            messages.error(request, 'Không thể hủy đặt phòng ở trạng thái này.')
    return redirect('accounts:profile')


@login_required
def booking_create_payment(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel'),
        pk=pk, user=request.user
    )
    method = (request.POST.get('method') or request.GET.get('method') or 'bank_transfer').strip()

    payment = (
        booking.payments
        .filter(status='pending', method=method)
        .order_by('-created_at')
        .first()
    )
    if not payment:
        payment = create_pending_payment_with_qr(booking=booking, method=method, request=request)

    if request.GET.get('format') == 'json' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'payment_id': payment.id,
            'booking_id': booking.id,
            'amount': str(payment.amount),
            'method': payment.method,
            'status': payment.status,
            'reference': payment.reference,
            'qr_url': payment.qr_url,
            'qr_payload': payment.qr_payload,
        })

    return redirect('bookings:payment_page', payment_id=payment.id)


@login_required
def payment_page(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related('booking__room__room_type__hotel'),
        pk=payment_id,
        booking__user=request.user,
    )
    return render(request, 'bookings/payment.html', {
        'payment': payment,
        'booking': payment.booking,
    })


@login_required
def payment_mark_paid(request, payment_id):
    """
    Chế độ demo: xác nhận đã thanh toán thủ công để đi tiếp luồng.
    """
    payment = get_object_or_404(
        Payment.objects.select_related('booking__room__room_type__hotel', 'booking__user'),
        pk=payment_id,
        booking__user=request.user,
    )
    if request.method != 'POST':
        return redirect('bookings:payment_page', payment_id=payment.id)

    if payment.status == 'paid':
        return redirect('bookings:detail', pk=payment.booking_id)

    payment.status = 'paid'
    payment.paid_at = timezone.now()
    try:
        payment.save()
    except ValidationError:
        pass

    booking = payment.booking
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()

    # Gửi email lúc đã thanh toán / hoàn tất
    send_booking_confirmation(booking)

    messages.success(request, f'✅ Thanh toán thành công cho booking #{booking.id}. Email đã được gửi.')
    return redirect('bookings:detail', pk=booking.id)


def _complete_payment_success(payment, *, gateway_payload=None, transaction_code=None):
    was_paid = payment.status == 'paid'
    if not was_paid:
        payment.status = 'paid'
        payment.paid_at = timezone.now()
        if transaction_code:
            payment.transaction_code = str(transaction_code)
        if gateway_payload is not None:
            payment.gateway_response = json.dumps(gateway_payload, ensure_ascii=False)
        payment.save()

    booking = payment.booking
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()

    # Gửi email đúng 1 lần khi vừa thanh toán xong
    if not was_paid:
        send_booking_confirmation(booking)


@require_GET
@login_required
def momo_return(request, payment_id):
    """
    RedirectUrl: người dùng quay về site sau khi thanh toán MoMo.
    """
    payment = get_object_or_404(
        Payment.objects.select_related('booking__room__room_type__hotel', 'booking__user'),
        pk=payment_id,
        booking__user=request.user,
    )

    data = request.GET.dict()
    ok_sig = momo.verify_result_signature(data)
    result_code = str(data.get('resultCode', ''))

    if ok_sig and result_code == '0':
        _complete_payment_success(payment, gateway_payload=data, transaction_code=data.get('transId'))
        messages.success(request, f'✅ Thanh toán MoMo thành công cho booking #{payment.booking_id}.')
        return redirect('bookings:detail', pk=payment.booking_id)

    messages.error(request, f'❌ Thanh toán MoMo chưa thành công: {data.get("message","")}')
    return redirect('bookings:payment_page', payment_id=payment.id)


@csrf_exempt
@require_POST
def momo_ipn(request):
    """
    IPN server-to-server từ MoMo.
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'result': 'bad_request'}, status=400)

    if not momo.verify_result_signature(payload):
        return JsonResponse({'result': 'invalid_signature'}, status=400)

    order_id = payload.get('orderId') or ''
    if not order_id:
        return JsonResponse({'result': 'missing_orderId'}, status=400)

    payment = Payment.objects.filter(reference=order_id).select_related('booking__room__room_type__hotel', 'booking__user').first()
    if not payment:
        return JsonResponse({'result': 'payment_not_found'}, status=404)

    if str(payload.get('resultCode', '')) == '0':
        _complete_payment_success(payment, gateway_payload=payload, transaction_code=payload.get('transId'))
        return JsonResponse({'result': 'ok'})

    # Lưu response để debug
    payment.gateway_response = json.dumps(payload, ensure_ascii=False)
    payment.status = 'failed'
    payment.save(update_fields=['gateway_response', 'status', 'updated_at'])
    return JsonResponse({'result': 'failed'})
