from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import Payment
from . import momo


def _absolute_url(request, path: str) -> str:
    if request is not None:
        return request.build_absolute_uri(path)
    base = getattr(settings, 'SITE_URL', '').rstrip('/')
    return f'{base}{path}' if base else path


def create_pending_payment_with_qr(*, booking, method: str = 'bank_transfer', request=None) -> Payment:
    """
    Tạo Payment trạng thái pending và gắn QR trỏ về trang thanh toán nội bộ.
    Không phụ thuộc thư viện tạo QR: dùng QR URL.
    """
    payment = Payment.objects.create(
        booking=booking,
        amount=booking.total_price,
        method=method,
        status='pending',
    )

    payment.reference = f'PAY{payment.id}-BOOK{booking.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
    payload = ''

    # MoMo: gọi API tạo payUrl, sau đó render QR từ payUrl
    if method == 'momo' and momo.get_momo_config():
        try:
            redirect_url = _absolute_url(request, reverse('bookings:momo_return', kwargs={'payment_id': payment.id}))
            ipn_url = _absolute_url(request, reverse('bookings:momo_ipn'))

            resp = momo.create_payment_link(
                order_id=payment.reference,
                request_id=payment.reference,
                amount=int(payment.amount),
                order_info=f"Thanh toán booking #{booking.id}",
                redirect_url=redirect_url,
                ipn_url=ipn_url,
                extra_data={"payment_id": payment.id, "booking_id": booking.id},
                lang="vi",
            )
            payment.gateway_response = json_dumps_safe(resp)
            pay_url = resp.get('payUrl') or resp.get('shortLink') or ''
            payload = pay_url
        except Exception as e:
            payment.gateway_response = f"MoMo error: {e}"
            payload = _absolute_url(
                request,
                reverse('bookings:payment_page', kwargs={'payment_id': payment.id}),
            )
    else:
        # Fallback: QR trỏ về trang payment nội bộ
        payload = _absolute_url(
            request,
            reverse('bookings:payment_page', kwargs={'payment_id': payment.id}),
        )

    payment.set_qr(payload)
    payment.save(update_fields=['reference', 'qr_payload', 'qr_url', 'gateway_response'])
    return payment


def json_dumps_safe(value):
    import json
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)
