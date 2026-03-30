"""
bookings/email_utils.py
Gửi email thông báo đặt phòng và hủy phòng qua Mailtrap.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation(booking):
    """
    Gửi email xác nhận đặt phòng đến khách hàng.
    Gọi ngay sau khi Booking được tạo thành công.
    """
    user  = booking.user
    hotel = booking.room.hotel

    if not user.email:
        logger.warning(f'Booking #{booking.id}: user {user.username} has no email, skip.')
        return False

    subject = f'✅ Xác nhận đặt phòng #{booking.id} — {hotel.name}'
    context = {'booking': booking}

    # Render HTML template
    html_content = render_to_string('emails/booking_confirmation.html', context)

    # Plain text fallback
    text_content = f"""
Xin chào {user.get_full_name() or user.username},

Đặt phòng của bạn đã được ghi nhận!

MÃ ĐẶT PHÒNG: #{booking.id}
Khách sạn   : {hotel.name}
Loại phòng  : {booking.room.room_type.name}
Số phòng    : {booking.room.room_number}
Check-in    : {booking.check_in.strftime('%d/%m/%Y')}
Check-out   : {booking.check_out.strftime('%d/%m/%Y')}
Số đêm      : {booking.nights()} đêm
Số khách    : {booking.num_guests} người
Tổng tiền   : {booking.total_price:,.0f} VNĐ
Trạng thái  : {booking.get_status_display()}

Trân trọng,
Hotel GIS
    """.strip()

    try:
        msg = EmailMultiAlternatives(
            subject      = subject,
            body         = text_content,
            from_email   = settings.DEFAULT_FROM_EMAIL,
            to           = [user.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send(fail_silently=False)
        logger.info(f'✅ Confirmation email sent → {user.email} (Booking #{booking.id})')
        return True

    except Exception as e:
        logger.error(f'❌ Failed to send confirmation email for Booking #{booking.id}: {e}')
        return False


def send_booking_cancellation(booking):
    """
    Gửi email thông báo hủy phòng đến khách hàng.
    Gọi sau khi cập nhật status = 'cancelled'.
    """
    user  = booking.user
    hotel = booking.room.hotel

    if not user.email:
        logger.warning(f'Booking #{booking.id}: user {user.username} has no email, skip.')
        return False

    subject = f'❌ Đặt phòng #{booking.id} đã được hủy — {hotel.name}'
    context = {'booking': booking}

    html_content = render_to_string('emails/booking_cancellation.html', context)

    text_content = f"""
Xin chào {user.get_full_name() or user.username},

Đặt phòng #{booking.id} của bạn tại {hotel.name} đã được hủy thành công.

Check-in  : {booking.check_in.strftime('%d/%m/%Y')}
Check-out : {booking.check_out.strftime('%d/%m/%Y')}
Tổng tiền : {booking.total_price:,.0f} VNĐ
{f"Lý do    : {booking.cancel_reason}" if booking.cancel_reason else ""}

Cảm ơn bạn đã sử dụng dịch vụ của Hotel GIS.

Trân trọng,
Hotel GIS
    """.strip()

    try:
        msg = EmailMultiAlternatives(
            subject    = subject,
            body       = text_content,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [user.email],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send(fail_silently=False)
        logger.info(f'✅ Cancellation email sent → {user.email} (Booking #{booking.id})')
        return True

    except Exception as e:
        logger.error(f'❌ Failed to send cancellation email for Booking #{booking.id}: {e}')
        return False