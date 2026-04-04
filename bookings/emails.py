"""
bookings/email.py
Gửi email xác nhận đặt phòng qua Mailtrap SMTP.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation(booking):
    """
    Gửi email xác nhận đặt phòng cho khách hàng.
    Gọi sau khi Booking đã được tạo thành công.

    Args:
        booking: instance của Booking (đã select_related đủ room → room_type → hotel)
    """
    recipient = booking.user.email
    if not recipient:
        logger.warning(f'Booking #{booking.id}: user không có email, bỏ qua gửi mail.')
        return

    subject = f'✅ Xác nhận đặt phòng #{booking.id} — {booking.room.hotel.name}'

    site_url = (getattr(settings, 'SITE_URL', '') or '').rstrip('/')
    booking_path = reverse('bookings:detail', kwargs={'pk': booking.id})
    booking_url = f'{site_url}{booking_path}' if site_url else booking_path

    context = {
        'booking':    booking,
        'hotel':      booking.room.hotel,
        'room_type':  booking.room.room_type,
        'room':       booking.room,
        'user':       booking.user,
        'nights':     booking.nights(),
        'booking_url': booking_url,
    }

    # Render cả 2 phiên bản text + HTML
    text_content = render_to_string('emails/booking_confirmation.txt', context)
    html_content = render_to_string('emails/booking_confirmation.html', context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    msg.attach_alternative(html_content, 'text/html')

    try:
        msg.send(fail_silently=False)
        logger.info(f'Booking #{booking.id}: đã gửi email xác nhận tới {recipient}')
    except Exception as e:
        # Không để lỗi mail làm crash booking
        logger.error(f'Booking #{booking.id}: gửi mail thất bại — {e}')
