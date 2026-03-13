from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from hotels.models import RoomType, Room
from .models import Booking
from .forms import BookingForm


@login_required
def create_booking(request, room_type_id):
    """
    Bước 1: Chọn ngày + số khách cho loại phòng.
    Bước 2: Xác nhận + submit → tự tìm 1 phòng available rồi tạo Booking.
    """
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
            messages.error(request, '😔 Không còn phòng trống cho loại phòng này trong khoảng thời gian đã chọn. Vui lòng thử ngày khác.')
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

        messages.success(request, f'🎉 Đặt phòng thành công! Mã đặt phòng: #{booking.id}')
        return redirect('bookings:detail', pk=booking.pk)

    # Tính số phòng còn trống (không kèm ngày — chỉ theo status)
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