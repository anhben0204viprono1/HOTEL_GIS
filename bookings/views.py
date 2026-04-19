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
from .models import Booking, Payment, AmenityUsage
from hotels.models import Amenity
from .forms import BookingForm, HourlyBookingForm
from . import momo as momo_service
from .emails import send_booking_confirmation


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

        # Tìm phòng còn trống chưa bị đặt chồng thời gian
        active_statuses = ['pending', 'confirmed', 'checked_in']

        daily_conflict_ids = Booking.objects.filter(
            room__room_type=room_type,
            status__in=active_statuses,
            booking_type="daily",
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).values_list('room_id', flat=True)

        from datetime import datetime, time as dt_time
        start_dt = timezone.make_aware(datetime.combine(check_in, dt_time.min))
        end_dt = timezone.make_aware(datetime.combine(check_out, dt_time.min))
        hourly_conflict_ids = Booking.objects.filter(
            room__room_type=room_type,
            status__in=active_statuses,
            booking_type="hourly",
            check_in_dt__lt=end_dt,
            check_out_dt__gt=start_dt,
        ).values_list("room_id", flat=True)

        booked_ids = set(daily_conflict_ids) | set(hourly_conflict_ids)

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


@login_required
def create_booking_hourly(request, room_type_id):
    """Đặt phòng theo giờ."""
    from datetime import timedelta

    room_type = get_object_or_404(RoomType, id=room_type_id, is_active=True)
    hotel = room_type.hotel
    form = HourlyBookingForm(request.POST or None, room_type=room_type)

    if request.method == "POST" and form.is_valid():
        check_in_dt = form.cleaned_data["check_in_dt"]
        check_out_dt = form.cleaned_data["check_out_dt"]
        num_guests = form.cleaned_data["num_guests"]
        note = form.cleaned_data["note"]

        # Normalize timezone-aware
        if timezone.is_naive(check_in_dt):
            check_in_dt = timezone.make_aware(check_in_dt)
        if timezone.is_naive(check_out_dt):
            check_out_dt = timezone.make_aware(check_out_dt)

        active_statuses = ["pending", "confirmed", "checked_in"]

        # Booking daily chặn theo ngày: [check_in, check_out)
        start_date = timezone.localtime(check_in_dt).date()
        end_date = timezone.localtime(check_out_dt).date()
        from datetime import time as dt_time
        end_exclusive = end_date
        if timezone.localtime(check_out_dt).time() != dt_time(0, 0):
            end_exclusive = end_date + timedelta(days=1)

        daily_conflict_room_ids = Booking.objects.filter(
            room__room_type=room_type,
            status__in=active_statuses,
            booking_type="daily",
            check_in__lt=end_exclusive,
            check_out__gt=start_date,
        ).values_list("room_id", flat=True)

        hourly_conflict_room_ids = Booking.objects.filter(
            room__room_type=room_type,
            status__in=active_statuses,
            booking_type="hourly",
            check_in_dt__lt=check_out_dt,
            check_out_dt__gt=check_in_dt,
        ).values_list("room_id", flat=True)

        conflict_ids = set(daily_conflict_room_ids) | set(hourly_conflict_room_ids)

        available_room = Room.objects.filter(
            room_type=room_type, status="available"
        ).exclude(id__in=conflict_ids).first()

        if not available_room:
            messages.error(request, "😔 Không còn phòng trống trong khung giờ này. Vui lòng thử lại.")
            return render(request, "bookings/create_hourly.html", {
                "form": form,
                "room_type": room_type,
                "hotel": hotel,
                "available_count": 0,
            })

        with transaction.atomic():
            booking = Booking.objects.create(
                user=request.user,
                room=available_room,
                booking_type="hourly",
                check_in_dt=check_in_dt,
                check_out_dt=check_out_dt,
                num_guests=num_guests,
                note=note,
                status="pending",
            )

        return redirect("bookings:payment", pk=booking.pk)

    available_count = Room.objects.filter(room_type=room_type, status="available").count()
    return render(request, "bookings/create_hourly.html", {
        "form": form,
        "room_type": room_type,
        "hotel": hotel,
        "available_count": available_count,
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
                was_paid = payment.status == 'paid'
                payment.status = 'paid'
                payment.transaction_code = order_id
                payment.note = f'transId MoMo: {trans_id}'
                payment.paid_at = timezone.now()
                payment.save()

                if booking.status == 'pending':
                    booking.status = 'confirmed'
                    booking.save()

                # Gửi email đúng 1 lần khi vừa thanh toán xong
                if not was_paid:
                    send_booking_confirmation(booking)
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
                was_paid = payment.status == 'paid'
                payment.status = 'paid'
                payment.note = f'transId MoMo: {trans_id}'
                payment.paid_at = timezone.now()
                payment.save()
                if booking.status == 'pending':
                    booking.status = 'confirmed'
                    booking.save()
                if not was_paid:
                    send_booking_confirmation(booking)
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


# ══════════════════════════════════════════════════════════════════════════════
# 9. TIỆN ÍCH KHI ĐANG Ở
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def amenity_usage_page(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("room__room_type__hotel", "user").prefetch_related(
            "room__room_type__amenities",
            "room__hotel__amenities",
            "amenity_usages__amenity",
        ),
        pk=pk,
        user=request.user,
    )

    if booking.status != "checked_in":
        messages.error(request, "Tiện ích chỉ khả dụng khi bạn đang ở (checked-in).")
        return redirect("bookings:detail", pk=pk)

    room_amenities = list(booking.room.room_type.amenities.all())
    hotel_amenities = list(booking.room.hotel.amenities.all())
    amenity_ids = {a.id for a in room_amenities}
    all_amenities = room_amenities + [a for a in hotel_amenities if a.id not in amenity_ids]

    usages = booking.amenity_usages.select_related("amenity").order_by("-used_at")

    return render(request, "bookings/amenities.html", {
        "booking": booking,
        "amenities": all_amenities,
        "usages": usages,
    })


@login_required
def amenity_use(request, pk, amenity_id):
    if request.method != "POST":
        return redirect("bookings:amenities", pk=pk)

    booking = get_object_or_404(
        Booking.objects.select_related("room__room_type__hotel", "user"),
        pk=pk,
        user=request.user,
    )
    if booking.status != "checked_in":
        messages.error(request, "Booking chưa ở (checked-in), không thể sử dụng tiện ích.")
        return redirect("bookings:detail", pk=pk)

    amenity = get_object_or_404(Amenity, pk=amenity_id)

    # Chỉ cho phép amenities thuộc hotel hoặc room_type
    allowed = (
        booking.room.room_type.amenities.filter(pk=amenity.pk).exists()
        or booking.room.hotel.amenities.filter(pk=amenity.pk).exists()
    )
    if not allowed:
        messages.error(request, "Tiện ích không thuộc khách sạn/phòng của booking này.")
        return redirect("bookings:amenities", pk=pk)

    try:
        qty = int(request.POST.get("quantity", "1") or "1")
    except ValueError:
        qty = 1
    qty = max(1, min(qty, 50))
    note = (request.POST.get("note", "") or "").strip()

    AmenityUsage.objects.create(
        booking=booking,
        user=request.user,
        amenity=amenity,
        quantity=qty,
        note=note,
        used_at=timezone.now(),
    )
    messages.success(request, f"Đã ghi nhận sử dụng tiện ích: {amenity.name}.")
    return redirect("bookings:amenities", pk=pk)
