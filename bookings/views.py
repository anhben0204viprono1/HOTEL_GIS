"""
bookings/views.py — đặt phòng theo ngày + theo giờ + thanh toán + review + tiện nghi + service request
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from datetime import datetime

from hotels.models import RoomType, Room, HotelService, ServiceRequest, Amenity
from .models import Booking, Payment, Review, AmenityUsage
from .forms import BookingForm, ReviewForm
from .email_utils import send_booking_confirmation, send_booking_cancellation


# ══════════════════════════════════════════════════════════════════════════════
# 1. TẠO ĐẶT PHÒNG THEO NGÀY
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def create_booking(request, room_type_id):
    room_type = get_object_or_404(RoomType, id=room_type_id, is_active=True)
    hotel     = room_type.hotel
    form      = BookingForm(request.POST or None, room_type=room_type)

    if request.method == 'POST' and form.is_valid():
        check_in   = form.cleaned_data['check_in']
        check_out  = form.cleaned_data['check_out']
        num_guests = form.cleaned_data['num_guests']
        note       = form.cleaned_data['note']

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
                booking_type='daily',
                check_in=check_in, check_out=check_out,
                num_guests=num_guests, note=note,
                total_price=total_price, status='pending',
            )

        return redirect('bookings:payment', pk=booking.pk)

    available_count = Room.objects.filter(
        room_type=room_type, status='available'
    ).count()

    return render(request, 'bookings/create.html', {
        'form': form, 'room_type': room_type,
        'hotel': hotel, 'available_count': available_count,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 2. TẠO ĐẶT PHÒNG THEO GIỜ
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def create_hourly_booking(request, room_type_id):
    room_type = get_object_or_404(RoomType, id=room_type_id, is_active=True)
    hotel     = room_type.hotel

    if request.method == 'POST':
        date_str     = request.POST.get('date', '').strip()
        time_in_str  = request.POST.get('time_in', '').strip()
        time_out_str = request.POST.get('time_out', '').strip()
        num_guests   = int(request.POST.get('num_guests', 1))
        note         = request.POST.get('note', '').strip()

        try:
            check_in_dt  = datetime.strptime(f'{date_str} {time_in_str}',  '%Y-%m-%d %H:%M')
            check_out_dt = datetime.strptime(f'{date_str} {time_out_str}', '%Y-%m-%d %H:%M')
            check_in_dt  = timezone.make_aware(check_in_dt)
            check_out_dt = timezone.make_aware(check_out_dt)
        except ValueError:
            messages.error(request, '⚠️ Thời gian không hợp lệ.')
            return render(request, 'bookings/create_hourly.html', {
                'room_type': room_type, 'hotel': hotel,
            })

        if check_out_dt <= check_in_dt:
            messages.error(request, '⚠️ Giờ trả phòng phải sau giờ nhận phòng.')
            return render(request, 'bookings/create_hourly.html', {
                'room_type': room_type, 'hotel': hotel,
            })

        # Tìm phòng trống (kiểm tra trùng giờ)
        booked_ids = Booking.objects.filter(
            room__room_type=room_type,
            booking_type='hourly',
            status__in=['pending', 'confirmed', 'checked_in'],
            check_in_dt__lt=check_out_dt,
            check_out_dt__gt=check_in_dt,
        ).values_list('room_id', flat=True)

        available_room = Room.objects.filter(
            room_type=room_type, status='available',
        ).exclude(id__in=booked_ids).first()

        if not available_room:
            messages.error(request,
                '😔 Không còn phòng trống trong khoảng thời gian này.')
            return render(request, 'bookings/create_hourly.html', {
                'room_type': room_type, 'hotel': hotel,
            })

        with transaction.atomic():
            booking = Booking(
                user=request.user, room=available_room,
                booking_type='hourly',
                check_in_dt=check_in_dt, check_out_dt=check_out_dt,
                num_guests=num_guests, note=note,
                status='pending',
            )
            booking.save()  # save() tự tính total_price

        return redirect('bookings:payment', pk=booking.pk)

    return render(request, 'bookings/create_hourly.html', {
        'room_type': room_type, 'hotel': hotel,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 3. TRANG THANH TOÁN
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def payment_page(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel', 'user'),
        pk=pk, user=request.user,
    )

    if booking.status not in ('pending',):
        return redirect('bookings:detail', pk=pk)

    # 👉 BỎ render payment.html
    return redirect('bookings:confirm_payment', pk=pk)

# ══════════════════════════════════════════════════════════════════════════════
# 4. XÁC NHẬN THANH TOÁN (nhấn nút là xong)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def confirm_payment(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user, status='pending')

    with transaction.atomic():
        Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            method='cash',
            status='paid',
            paid_at=timezone.now(),
            note='Auto payment (no gateway)',
        )
        booking.status = 'confirmed'
        booking.save()

    # Gửi email xác nhận qua Mailtrap
    send_booking_confirmation(booking)

    messages.success(request,
        f'🎉 Đặt phòng #{booking.id} đã được xác nhận!')
    return redirect('bookings:payment_result', pk=pk)


@login_required
def payment_result(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel'),
        pk=pk, user=request.user,
    )
    last_payment = booking.payments.order_by('-created_at').first()
    success      = last_payment and last_payment.status == 'paid'
    return render(request, 'bookings/payment_result.html', {
        'booking': booking, 'last_payment': last_payment, 'success': success,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 5. CHI TIẾT BOOKING
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
            booking.status        = 'cancelled'
            booking.cancelled_at  = timezone.now()
            booking.cancel_reason = request.POST.get('reason', '').strip()
            booking.save()
            # Gửi email thông báo hủy
            send_booking_cancellation(booking)
            messages.warning(request, f'Đặt phòng #{booking.id} đã được hủy.')
        else:
            messages.error(request, 'Không thể hủy đặt phòng ở trạng thái này.')
    return redirect('accounts:profile')


@login_required
def my_bookings(request):
    bookings = (
        request.user.bookings
        .select_related('room__room_type__hotel')
        .order_by('-created_at')
    )
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


# ══════════════════════════════════════════════════════════════════════════════
# 6. CREATE REVIEW
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def create_review(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel'),
        pk=pk, user=request.user,
    )

    # ── Kiểm tra điều kiện: phải checked_out mới được đánh giá ──────────────
    if booking.status != 'checked_out':
        messages.error(request,
            '⚠️ Bạn chỉ có thể viết đánh giá sau khi đã trả phòng (checked out).')
        return redirect('bookings:detail', pk=pk)

    # Kiểm tra đã đánh giá chưa
    try:
        booking.review
        messages.info(request, 'ℹ️ Bạn đã đánh giá booking này rồi.')
        return redirect('bookings:detail', pk=pk)
    except Exception:
        pass  # Chưa có review — tiếp tục

    hotel = booking.room.hotel
    form  = ReviewForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        Review.objects.create(
            booking=booking, user=request.user, hotel=hotel,
            rating=form.cleaned_data['rating'],
            comment=form.cleaned_data['comment'],
        )
        messages.success(request, f'⭐ Cảm ơn bạn đã đánh giá {hotel.name}!')
        return redirect('bookings:detail', pk=pk)

    return render(request, 'bookings/review_form.html', {
        'booking': booking, 'hotel': hotel, 'form': form,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 7. TIỆN NGHI SỬ DỤNG KHI ĐANG Ở
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def amenity_usage(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related('room__room_type__hotel'),
        pk=pk, user=request.user,
    )

    if booking.status not in ('confirmed', 'checked_in'):
        messages.error(request, '⚠️ Chỉ ghi nhận tiện nghi khi đã check-in.')
        return redirect('bookings:detail', pk=pk)

    hotel          = booking.room.hotel
    hotel_amenities = hotel.amenities.all().order_by('category', 'name')
    usages         = booking.amenity_usages.select_related('amenity').order_by('-used_at')

    if request.method == 'POST':
        amenity_id = request.POST.get('amenity_id')
        quantity   = int(request.POST.get('quantity', 1))
        note       = request.POST.get('note', '').strip()
        amenity    = get_object_or_404(Amenity, pk=amenity_id)
        AmenityUsage.objects.create(
            booking=booking, amenity=amenity,
            quantity=max(1, quantity), note=note,
        )
        messages.success(request, f'✅ Đã ghi nhận sử dụng "{amenity.name}".')
        return redirect('bookings:amenity_usage', pk=pk)

    return render(request, 'bookings/amenity_usage.html', {
        'booking': booking, 'hotel': hotel,
        'hotel_amenities': hotel_amenities, 'usages': usages,
    })


# ══════════════════════════════════════════════════════════════════════════════
# 8. SERVICE REQUEST
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def booking_detail_user(request, pk):
    booking = get_object_or_404(
        request.user.bookings.select_related('room__room_type__hotel', 'room__hotel'),
        pk=pk
    )
    hotel = booking.room.hotel
    services = HotelService.objects.filter(
        hotel=hotel, is_available=True
    ).order_by('category', 'order', 'name')
    my_requests = ServiceRequest.objects.filter(
        room=booking.room, guest=request.user,
    ).select_related('service').order_by('-created_at')

    return render(request, 'bookings/booking_detail_user.html', {
        'booking':     booking,
        'hotel':       hotel,
        'services':    services,
        'my_requests': my_requests,
    })


@login_required
def submit_service_request(request, booking_pk):
    booking = get_object_or_404(
        request.user.bookings.select_related('room__hotel'),
        pk=booking_pk
    )
    if booking.status not in ('confirmed', 'checked_in'):
        messages.error(request, '⚠️ Chỉ có thể gửi yêu cầu khi booking đã xác nhận hoặc đang ở.')
        return redirect('bookings:detail_user', pk=booking_pk)

    if request.method == 'POST':
        service_id   = request.POST.get('service', '').strip()
        note         = request.POST.get('note', '').strip()
        quantity_raw = request.POST.get('quantity', '1')
        priority_raw = request.POST.get('priority', 'normal')
        priority     = priority_raw if priority_raw in ('normal', 'urgent') else 'normal'

        if not service_id:
            messages.error(request, '⚠️ Vui lòng chọn loại dịch vụ.')
            return redirect('bookings:detail_user', pk=booking_pk)

        try:
            service = HotelService.objects.get(
                pk=service_id, hotel=booking.room.hotel, is_available=True
            )
        except HotelService.DoesNotExist:
            messages.error(request, '⚠️ Dịch vụ không hợp lệ.')
            return redirect('bookings:detail_user', pk=booking_pk)

        try:
            quantity = max(1, int(quantity_raw))
        except ValueError:
            quantity = 1

        ServiceRequest.objects.create(
            room=booking.room, service=service,
            guest=request.user,
            guest_name=request.user.get_full_name() or request.user.username,
            note=note, quantity=quantity, priority=priority, status='pending',
        )
        messages.success(request, f'✅ Đã gửi yêu cầu "{service.name}"! Nhân viên sẽ xử lý sớm.')

    return redirect('bookings:detail_user', pk=booking_pk)