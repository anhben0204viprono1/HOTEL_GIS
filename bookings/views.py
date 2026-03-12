from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from hotels.models import Room
from .models import Booking
from .forms import BookingForm


@login_required
def create_booking(request, room_id):
    room = get_object_or_404(Room, id=room_id, status='available')
    form = BookingForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.user = request.user
        booking.room = room
        booking.save()
        messages.success(request, f'🎉 Đặt phòng thành công! Mã đặt phòng: #{booking.id}')
        return redirect('bookings:detail', pk=booking.pk)

    context = {'form': form, 'room': room, 'hotel': room.hotel}
    return render(request, 'bookings/create.html', context)


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, 'bookings/detail.html', {'booking': booking})


@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.can_cancel():
        booking.status       = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancel_reason = request.POST.get('reason', '')
        booking.save()
        messages.warning(request, f'Đặt phòng #{booking.id} đã được hủy.')
    return redirect('accounts:profile')