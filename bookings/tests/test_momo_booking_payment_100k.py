from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from hotels.models import Hotel, RoomType, Room
from bookings.models import Booking, Payment


class MoMoBookingPayment100kTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="pass12345",
        )

        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            address="1 Test Street",
            city="Hồ Chí Minh",
            latitude=Decimal("10.77386000"),
            longitude=Decimal("106.70454900"),
            star_rating=3,
            is_active=True,
        )

        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard",
            max_occupancy=2,
            price_per_night=Decimal("100000"),
            is_active=True,
        )

        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number="101",
            floor=1,
            status="available",
        )

        today = timezone.localdate()
        self.booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=today,
            check_out=today + timedelta(days=1),
            num_guests=1,
            status="pending",
        )

    @patch("bookings.views.momo_service.create_payment")
    def test_initiate_momo_creates_pending_payment_100k_and_redirects(self, mock_create_payment):
        mock_create_payment.return_value = {
            "ok": True,
            "pay_url": "https://test-payment.momo.vn/pay/FAKE",
            "message": "",
            "order_id": "ORDER-123",
            "request_id": "REQ-123",
        }

        self.client.login(username="testuser", password="pass12345")

        url = reverse("bookings:momo_init", kwargs={"pk": self.booking.pk})
        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "https://test-payment.momo.vn/pay/FAKE")

        payment = Payment.objects.filter(booking=self.booking, method="momo").order_by("-created_at").first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.amount, Decimal("100000.00"))
        self.assertEqual(payment.transaction_code, "ORDER-123")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="Hotel GIS <noreply@example.com>",
        SITE_URL="http://testserver",
    )
    @patch("bookings.views.momo_service.verify_ipn", return_value=True)
    def test_momo_ipn_success_marks_paid_confirms_booking_and_sends_email(self, _mock_verify):
        # Create pending MoMo payment (100k) for this booking
        payment = Payment.objects.create(
            booking=self.booking,
            amount=Decimal("100000"),
            method="momo",
            status="pending",
            transaction_code="ORDER-OK",
        )

        url = reverse("bookings:momo_ipn", kwargs={"pk": self.booking.pk})
        payload = {
            "resultCode": 0,
            "orderId": "ORDER-OK",
            "transId": "TRANS-1",
            "message": "Success",
            "signature": "ignored-in-test",
        }

        resp = self.client.post(url, data=json_dump(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)

        payment.refresh_from_db()
        self.booking.refresh_from_db()
        self.assertEqual(payment.status, "paid")
        self.assertIsNotNone(payment.paid_at)
        self.assertEqual(self.booking.status, "confirmed")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Xác nhận đặt phòng", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

        # IPN called again should not resend email
        resp2 = self.client.post(url, data=json_dump(payload), content_type="application/json")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)


def json_dump(value) -> str:
    import json
    return json.dumps(value)
