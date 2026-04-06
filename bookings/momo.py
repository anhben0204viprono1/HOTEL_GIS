"""
bookings/momo.py
Tích hợp thanh toán MoMo Payment Gateway v2 (HMAC-SHA256).

Tài liệu: https://developers.momo.vn/v3/docs/payment/api/
Sandbox:   https://test-payment.momo.vn/v2/gateway/api/create
Prod:      https://payment.momo.vn/v2/gateway/api/create
"""
import hashlib
import hmac
import json
import uuid
import urllib.request
import urllib.error
from django.conf import settings


# ─── Cấu hình MoMo ───────────────────────────────────────────────────────────

MOMO_ENDPOINT  = getattr(settings, 'MOMO_ENDPOINT',
    'https://test-payment.momo.vn/v2/gateway/api/create')

MOMO_PARTNER_CODE = getattr(settings, 'MOMO_PARTNER_CODE', 'MOMO')
MOMO_ACCESS_KEY   = getattr(settings, 'MOMO_ACCESS_KEY',   'F8BBA842ECF85')
MOMO_SECRET_KEY   = getattr(settings, 'MOMO_SECRET_KEY',   'K951B6PE1waDMi640xX08PD3vg6EkVlz')


# ─── Helper ───────────────────────────────────────────────────────────────────

def _sign(raw: str) -> str:
    """Tạo chữ ký HMAC-SHA256."""
    return hmac.new(
        MOMO_SECRET_KEY.encode('utf-8'),
        raw.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def create_payment(booking, redirect_url: str, ipn_url: str) -> dict:
    """
    Gọi API MoMo để tạo link thanh toán.

    Returns:
        dict với keys: ok (bool), pay_url (str), message (str)
    """
    request_id = str(uuid.uuid4())
    order_id   = f'HOTEL-{booking.id}-{request_id[:8]}'
    amount     = int(booking.total_price)          # MoMo nhận int (VNĐ)
    order_info = (
        f'Đặt phòng #{booking.id} — '
        f'{booking.room.hotel.name} '
        f'({booking.check_in} → {booking.check_out})'
    )
    extra_data = ''                                # Base64 nếu cần truyền thêm
    request_type = 'captureWallet'                    # hoặc 'captureWallet' cho ví MoMo

    # ── Tạo raw_signature đúng thứ tự alphabet ──────────────────────────────
    raw = (
        f'accessKey={MOMO_ACCESS_KEY}'
        f'&amount={amount}'
        f'&extraData={extra_data}'
        f'&ipnUrl={ipn_url}'
        f'&orderId={order_id}'
        f'&orderInfo={order_info}'
        f'&partnerCode={MOMO_PARTNER_CODE}'
        f'&redirectUrl={redirect_url}'
        f'&requestId={request_id}'
        f'&requestType={request_type}'
    )
    signature = _sign(raw)

    payload = {
        'partnerCode': MOMO_PARTNER_CODE,
        'accessKey':   MOMO_ACCESS_KEY,
        'requestId':   request_id,
        'amount':      amount,
        'orderId':     order_id,
        'orderInfo':   order_info,
        'redirectUrl': redirect_url,
        'ipnUrl':      ipn_url,
        'extraData':   extra_data,
        'requestType': request_type,
        'signature':   signature,
        'lang':        'vi',
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req  = urllib.request.Request(
            MOMO_ENDPOINT,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))

        if result.get('resultCode') == 0:
            return {
                'ok':      True,
                'pay_url': result.get('payUrl', ''),
                'message': result.get('message', ''),
                'order_id': order_id,
                'request_id': request_id,
            }
        return {
            'ok':      False,
            'pay_url': '',
            'message': result.get('message', 'Lỗi từ MoMo'),
            'order_id': order_id,
        }

    except urllib.error.URLError as e:
        return {'ok': False, 'pay_url': '', 'message': f'Không kết nối được MoMo: {e.reason}'}
    except Exception as e:
        return {'ok': False, 'pay_url': '', 'message': str(e)}


def verify_ipn(data: dict) -> bool:
    """
    Xác thực chữ ký IPN từ MoMo gửi về.
    data: dict từ request.POST hoặc request body JSON.
    """
    raw = (
        f'accessKey={MOMO_ACCESS_KEY}'
        f'&amount={data.get("amount", "")}'
        f'&extraData={data.get("extraData", "")}'
        f'&message={data.get("message", "")}'
        f'&orderId={data.get("orderId", "")}'
        f'&orderInfo={data.get("orderInfo", "")}'
        f'&orderType={data.get("orderType", "")}'
        f'&partnerCode={data.get("partnerCode", "")}'
        f'&payType={data.get("payType", "")}'
        f'&requestId={data.get("requestId", "")}'
        f'&responseTime={data.get("responseTime", "")}'
        f'&resultCode={data.get("resultCode", "")}'
        f'&transId={data.get("transId", "")}'
    )
    expected = _sign(raw)
    return hmac.compare_digest(expected, data.get('signature', ''))