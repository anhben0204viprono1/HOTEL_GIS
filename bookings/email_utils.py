"""
bookings/email_utils.py
Gửi email thông báo đặt phòng và hủy phòng qua Mailtrap.
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def _format_checkin_checkout(booking):
    """
    Trả về tuple (checkin_str, checkout_str, duration_str) cho cả daily/hourly.
    - Daily: dd/mm/YYYY + "<n> đêm"
    - Hourly: dd/mm/YYYY HH:MM + "<n> giờ"
    """
    if getattr(booking, 'booking_type', None) == 'hourly':
        check_in  = getattr(booking, 'check_in_dt', None)
        check_out = getattr(booking, 'check_out_dt', None)
        fmt = '%d/%m/%Y %H:%M'
        checkin_str  = check_in.strftime(fmt) if check_in else '—'
        checkout_str = check_out.strftime(fmt) if check_out else '—'
        duration_str = f'{booking.hours()} giờ'
        return checkin_str, checkout_str, duration_str

    check_in  = getattr(booking, 'check_in', None)
    check_out = getattr(booking, 'check_out', None)
    fmt = '%d/%m/%Y'
    checkin_str  = check_in.strftime(fmt) if check_in else '—'
    checkout_str = check_out.strftime(fmt) if check_out else '—'
    duration_str = f'{booking.nights()} đêm'
    return checkin_str, checkout_str, duration_str


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

    checkin_str, checkout_str, duration_str = _format_checkin_checkout(booking)

    # Plain text fallback
    text_content = f"""
Xin chào {user.get_full_name() or user.username},

Đặt phòng của bạn đã được ghi nhận!

MÃ ĐẶT PHÒNG: #{booking.id}
Khách sạn   : {hotel.name}
Loại phòng  : {booking.room.room_type.name}
Số phòng    : {booking.room.room_number}
Check-in    : {checkin_str}
Check-out   : {checkout_str}
Thời lượng  : {duration_str}
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

    checkin_str, checkout_str, duration_str = _format_checkin_checkout(booking)

    text_content = f"""
Xin chào {user.get_full_name() or user.username},

Đặt phòng #{booking.id} của bạn tại {hotel.name} đã được hủy thành công.

Check-in  : {checkin_str}
Check-out : {checkout_str}
Thời lượng: {duration_str}
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

def send_password_changed(user):
    """
    Gửi email thông báo đổi mật khẩu thành công.
    Gọi sau khi user đổi mật khẩu thành công.
    """
    if not user.email:
        return False

    from django.utils import timezone
    changed_at = timezone.localtime().strftime('%H:%M — %d/%m/%Y')

    subject = '🔐 Mật khẩu tài khoản Hotel GIS đã được thay đổi'

    text_content = f"""
Xin chào {user.get_full_name() or user.username},

Mật khẩu tài khoản của bạn tại Hotel GIS vừa được thay đổi thành công lúc {changed_at}.

Nếu bạn KHÔNG thực hiện thao tác này, vui lòng liên hệ ngay với chúng tôi hoặc đặt lại mật khẩu tại:
  http://127.0.0.1:8000/accounts/password-reset/

Trân trọng,
Hotel GIS
    """.strip()

    html_content = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);">

    <!-- Header -->
    <div style="background:#1A1A2E;padding:28px 32px;text-align:center;">
      <span style="font-size:28px;">🔐</span>
      <h1 style="color:#C9A84C;font-size:20px;margin:8px 0 0;letter-spacing:1px;">MẬT KHẨU ĐÃ ĐƯỢC THAY ĐỔI</h1>
      <p style="color:#aaa;font-size:12px;margin:4px 0 0;">Hotel GIS — Bảo mật tài khoản</p>
    </div>

    <!-- Body -->
    <div style="padding:32px;">
      <p style="font-size:15px;color:#333;margin:0 0 16px;">
        Xin chào <strong>{user.get_full_name() or user.username}</strong>,
      </p>
      <p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 20px;">
        Mật khẩu tài khoản của bạn tại <strong>Hotel GIS</strong> vừa được thay đổi thành công lúc
        <strong style="color:#1A1A2E;">{changed_at}</strong>.
      </p>

      <!-- Warning box -->
      <div style="background:#fff8e6;border-left:4px solid #C9A84C;border-radius:6px;padding:16px 20px;margin-bottom:24px;">
        <p style="margin:0;font-size:13px;color:#7a5c00;line-height:1.6;">
          ⚠️ <strong>Không phải bạn?</strong> Nếu bạn không thực hiện thao tác này, tài khoản của bạn có thể đã bị xâm phạm.
          Hãy đặt lại mật khẩu ngay.
        </p>
      </div>

      <div style="text-align:center;margin-bottom:24px;">
        <a href="http://127.0.0.1:8000/accounts/password-reset/"
           style="display:inline-block;background:#C9A84C;color:#1A1A2E;text-decoration:none;
                  padding:12px 32px;border-radius:8px;font-weight:700;font-size:14px;letter-spacing:.5px;">
          Đặt lại mật khẩu ngay
        </a>
      </div>

      <p style="font-size:13px;color:#999;text-align:center;margin:0;">
        Nếu bạn đã thực hiện thay đổi này, bạn có thể bỏ qua email này.
      </p>
    </div>

    <!-- Footer -->
    <div style="background:#f8f6f2;padding:16px 32px;text-align:center;border-top:1px solid #eee;">
      <p style="margin:0;font-size:11px;color:#aaa;">
        © 2026 Hotel GIS · TP. Hồ Chí Minh · Không trả lời email này
      </p>
    </div>
  </div>
</body>
</html>
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
        logger.info(f'✅ Password-changed email sent → {user.email}')
        return True
    except Exception as e:
        logger.error(f'❌ Failed to send password-changed email to {user.email}: {e}')
        return False
