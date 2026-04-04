import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.conf import settings


@dataclass(frozen=True)
class MoMoConfig:
    endpoint: str
    partner_code: str
    access_key: str
    secret_key: str
    store_id: str


def get_momo_config() -> Optional[MoMoConfig]:
    if not getattr(settings, 'MOMO_ENABLED', False):
        return None

    partner_code = getattr(settings, 'MOMO_PARTNER_CODE', '').strip()
    access_key = getattr(settings, 'MOMO_ACCESS_KEY', '').strip()
    secret_key = getattr(settings, 'MOMO_SECRET_KEY', '').strip()
    endpoint = getattr(settings, 'MOMO_ENDPOINT', '').strip().rstrip('/')
    store_id = getattr(settings, 'MOMO_STORE_ID', '').strip() or 'HotelGIS'

    if not (partner_code and access_key and secret_key and endpoint):
        return None

    return MoMoConfig(
        endpoint=endpoint,
        partner_code=partner_code,
        access_key=access_key,
        secret_key=secret_key,
        store_id=store_id,
    )


def _hmac_sha256_hex(secret_key: str, raw: str) -> str:
    return hmac.new(secret_key.encode('utf-8'), raw.encode('utf-8'), hashlib.sha256).hexdigest()


def _b64_extra_data(data: Dict[str, Any]) -> str:
    if not data:
        return ""
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return base64.b64encode(raw).decode('ascii')


def create_payment_link(*, order_id: str, request_id: str, amount: int, order_info: str, redirect_url: str, ipn_url: str, extra_data: Optional[Dict[str, Any]] = None, lang: str = "vi") -> Dict[str, Any]:
    """
    Tạo payment link theo MoMo Collection Link: POST /v2/gateway/api/create (requestType=payWithMethod).
    Trả về JSON response (chứa payUrl/shortLink/resultCode/message...).
    """
    cfg = get_momo_config()
    if not cfg:
        raise RuntimeError("MoMo is not configured (missing settings).")

    extra_data_b64 = _b64_extra_data(extra_data or {})
    request_type = "payWithMethod"

    raw_signature = (
        f"accessKey={cfg.access_key}"
        f"&amount={amount}"
        f"&extraData={extra_data_b64}"
        f"&ipnUrl={ipn_url}"
        f"&orderId={order_id}"
        f"&orderInfo={order_info}"
        f"&partnerCode={cfg.partner_code}"
        f"&redirectUrl={redirect_url}"
        f"&requestId={request_id}"
        f"&requestType={request_type}"
    )
    signature = _hmac_sha256_hex(cfg.secret_key, raw_signature)

    payload = {
        "partnerCode": cfg.partner_code,
        "partnerName": "Hotel GIS",
        "storeId": cfg.store_id,
        "requestId": request_id,
        "amount": int(amount),
        "orderId": order_id,
        "orderInfo": order_info,
        "redirectUrl": redirect_url,
        "ipnUrl": ipn_url,
        "lang": lang,
        "requestType": request_type,
        "extraData": extra_data_b64,
        "signature": signature,
    }

    url = f"{cfg.endpoint}/v2/gateway/api/create"
    req = Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (HTTPError, URLError) as e:
        raise RuntimeError(f"MoMo request failed: {e}")


def verify_result_signature(data: Dict[str, Any]) -> bool:
    """
    Verify signature của redirectUrl/ipnUrl payload theo doc.
    """
    cfg = get_momo_config()
    if not cfg:
        return False

    signature = (data.get("signature") or "").strip()
    if not signature:
        return False

    raw = (
        f"accessKey={cfg.access_key}"
        f"&amount={data.get('amount','')}"
        f"&extraData={data.get('extraData','')}"
        f"&message={data.get('message','')}"
        f"&orderId={data.get('orderId','')}"
        f"&orderInfo={data.get('orderInfo','')}"
        f"&orderType={data.get('orderType','')}"
        f"&partnerCode={data.get('partnerCode','')}"
        f"&payType={data.get('payType','')}"
        f"&requestId={data.get('requestId','')}"
        f"&responseTime={data.get('responseTime','')}"
        f"&resultCode={data.get('resultCode','')}"
        f"&transId={data.get('transId','')}"
    )
    expected = _hmac_sha256_hex(cfg.secret_key, raw)
    return hmac.compare_digest(expected, signature)
