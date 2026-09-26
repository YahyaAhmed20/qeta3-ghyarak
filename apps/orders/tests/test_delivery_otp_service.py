import pytest

from apps.orders.constants import OrderStatus
from apps.orders.models import DeliveryOTP


@pytest.mark.django_db
def test_delivery_otp_can_be_created(order):
    from django.utils import timezone
    from datetime import timedelta

    otp = DeliveryOTP.objects.create(
        order=order,
        code_hash="test-hash",
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    assert otp.order_id == order.id
    assert otp.status == "ACTIVE"
    assert otp.attempts == 0
    assert otp.max_attempts == 5
    assert otp.verified_at is None


@pytest.mark.django_db
def test_delivery_otp_service_generates_hashed_code(
    order,
    seller_owner,
):
    from apps.orders.services.delivery_otp import DeliveryOTPService

    order.status = OrderStatus.OUT_FOR_DELIVERY
    order.save(update_fields=["status", "updated_at"])

    otp, code = DeliveryOTPService.create(order=order)

    assert len(code) == 6
    assert code.isdigit()

    assert otp.order_id == order.id
    assert otp.status == "ACTIVE"
    assert otp.attempts == 0
    assert otp.max_attempts == 5

    assert otp.code_hash != code


@pytest.mark.django_db
def test_delivery_otp_service_verifies_code_and_is_single_use(order):
    from apps.orders.services.delivery_otp import DeliveryOTPService

    order.status = OrderStatus.OUT_FOR_DELIVERY
    order.save(update_fields=["status", "updated_at"])

    otp, code = DeliveryOTPService.create(order=order)

    verified = DeliveryOTPService.verify(
        order=order,
        otp_id=otp.id,
        code=code,
    )

    assert verified.id == otp.id
    assert verified.status == "VERIFIED"
    assert verified.verified_at is not None

    with pytest.raises(ValueError, match="not active"):
        DeliveryOTPService.verify(
            order=order,
            otp_id=otp.id,
            code=code,
        )


@pytest.mark.django_db
def test_delivery_otp_blocks_after_max_attempts(order):
    from apps.orders.services.delivery_otp import DeliveryOTPService

    order.status = OrderStatus.OUT_FOR_DELIVERY
    order.save(update_fields=["status", "updated_at"])

    otp, code = DeliveryOTPService.create(order=order)

    for _ in range(4):
        with pytest.raises(ValueError, match="Invalid delivery OTP."):
            DeliveryOTPService.verify(
                order=order,
                otp_id=otp.id,
                code="000000",
            )

    otp.refresh_from_db()

    assert otp.attempts == 4
    assert otp.status == "ACTIVE"

    with pytest.raises(ValueError, match="Invalid delivery OTP."):
        DeliveryOTPService.verify(
            order=order,
            otp_id=otp.id,
            code="000000",
        )

    otp.refresh_from_db()

    assert otp.attempts == 5
    assert otp.status == "BLOCKED"

    with pytest.raises(ValueError, match="not active"):
        DeliveryOTPService.verify(
            order=order,
            otp_id=otp.id,
            code=code,
        )


@pytest.mark.django_db
def test_delivery_otp_expires_after_expiration(order):
    from datetime import timedelta

    from django.utils import timezone

    from apps.orders.services.delivery_otp import DeliveryOTPService

    order.status = OrderStatus.OUT_FOR_DELIVERY
    order.save(update_fields=["status", "updated_at"])

    otp, code = DeliveryOTPService.create(order=order)

    otp.expires_at = timezone.now() - timedelta(seconds=1)
    otp.save(update_fields=["expires_at", "updated_at"])

    with pytest.raises(
        ValueError,
        match="Delivery OTP has expired.",
    ):
        DeliveryOTPService.verify(
            order=order,
            otp_id=otp.id,
            code=code,
        )

    otp.refresh_from_db()

    assert otp.status == "EXPIRED"


@pytest.mark.django_db
def test_creating_new_delivery_otp_invalidates_previous_one(order):
    from apps.orders.services.delivery_otp import DeliveryOTPService

    order.status = OrderStatus.OUT_FOR_DELIVERY
    order.save(update_fields=["status", "updated_at"])

    old_otp, old_code = DeliveryOTPService.create(order=order)

    new_otp, new_code = DeliveryOTPService.create(order=order)

    old_otp.refresh_from_db()
    new_otp.refresh_from_db()

    assert old_otp.id != new_otp.id
    assert old_otp.status == "EXPIRED"
    assert new_otp.status == "ACTIVE"

    with pytest.raises(ValueError, match="not active"):
        DeliveryOTPService.verify(
            order=order,
            otp_id=old_otp.id,
            code=old_code,
        )

    verified = DeliveryOTPService.verify(
        order=order,
        otp_id=new_otp.id,
        code=new_code,
    )

    assert verified.id == new_otp.id
    assert verified.status == "VERIFIED"