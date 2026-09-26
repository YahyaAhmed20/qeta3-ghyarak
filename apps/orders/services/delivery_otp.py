import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from apps.orders.constants import OrderStatus
from apps.orders.models import DeliveryOTP


class DeliveryOTPService:

    OTP_LENGTH = 6
    EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 5

    @staticmethod
    def _generate_code():
        return f"{secrets.randbelow(1_000_000):06d}"

    @classmethod
    @transaction.atomic
    def create(cls, *, order):
        if order.status != OrderStatus.OUT_FOR_DELIVERY:
            raise ValueError(
                "Delivery OTP can only be created for orders "
                "that are out for delivery."
            )

        existing = DeliveryOTP.objects.filter(
            order=order,
            status="ACTIVE",
        ).first()

        if existing:
            existing.status = "EXPIRED"
            existing.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        code = cls._generate_code()

        otp = DeliveryOTP.objects.create(
            order=order,
            code_hash=make_password(code),
            status="ACTIVE",
            attempts=0,
            max_attempts=cls.MAX_ATTEMPTS,
            expires_at=timezone.now()
            + timedelta(minutes=cls.EXPIRY_MINUTES),
        )

        return otp, code

    @classmethod
    def verify(cls, *, order, otp_id, code):
        error = None
        verified_otp = None

        with transaction.atomic():
            otp = (
                DeliveryOTP.objects
                .select_for_update()
                .filter(
                    id=otp_id,
                    order=order,
                )
                .first()
            )

            if otp is None:
                error = "Delivery OTP not found."

            elif otp.status != "ACTIVE":
                error = "Delivery OTP is not active."

            else:
                now = timezone.now()

                if now >= otp.expires_at:
                    otp.status = "EXPIRED"
                    otp.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )
                    error = "Delivery OTP has expired."

                elif otp.attempts >= otp.max_attempts:
                    otp.status = "BLOCKED"
                    otp.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )
                    error = "Delivery OTP is blocked."

                elif not check_password(code, otp.code_hash):
                    otp.attempts += 1

                    if otp.attempts >= otp.max_attempts:
                        otp.status = "BLOCKED"

                    otp.save(
                        update_fields=[
                            "attempts",
                            "status",
                            "updated_at",
                        ]
                    )

                    error = "Invalid delivery OTP."

                else:
                    otp.status = "VERIFIED"
                    otp.verified_at = now

                    otp.save(
                        update_fields=[
                            "status",
                            "verified_at",
                            "updated_at",
                        ]
                    )

                    verified_otp = otp

        if error:
            raise ValueError(error)

        return verified_otp

    @classmethod
    def validate_for_delivery(
        cls,
        *,
        order,
        otp_id,
        code,
    ):
        """
        Validate OTP before starting the delivery transaction.

        Invalid attempts are committed independently.

        On success, the OTP remains ACTIVE.
        The caller must verify it inside the final delivery transaction.
        """

        error = None

        with transaction.atomic():
            otp = (
                DeliveryOTP.objects
                .select_for_update()
                .filter(
                    id=otp_id,
                    order=order,
                )
                .first()
            )

            if otp is None:
                error = "Delivery OTP not found."

            elif otp.status != "ACTIVE":
                error = "Delivery OTP is not active."

            else:
                now = timezone.now()

                if now >= otp.expires_at:
                    otp.status = "EXPIRED"

                    otp.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

                    error = "Delivery OTP has expired."

                elif otp.attempts >= otp.max_attempts:
                    otp.status = "BLOCKED"

                    otp.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

                    error = "Delivery OTP is blocked."

                elif not check_password(
                    code,
                    otp.code_hash,
                ):
                    otp.attempts += 1

                    if otp.attempts >= otp.max_attempts:
                        otp.status = "BLOCKED"

                    otp.save(
                        update_fields=[
                            "attempts",
                            "status",
                            "updated_at",
                        ]
                    )

                    error = "Invalid delivery OTP."

        if error:
            raise ValueError(error)

        return otp.id

    @classmethod
    def validate_code(cls, *, order, otp_id, code):
        otp = (
            DeliveryOTP.objects
            .select_for_update()
            .filter(
                id=otp_id,
                order=order,
            )
            .first()
        )

        if otp is None:
            raise ValueError("Delivery OTP not found.")

        if otp.status != "ACTIVE":
            raise ValueError("Delivery OTP is not active.")

        now = timezone.now()

        if now >= otp.expires_at:
            otp.status = "EXPIRED"
            otp.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )
            raise ValueError("Delivery OTP has expired.")

        if otp.attempts >= otp.max_attempts:
            otp.status = "BLOCKED"
            otp.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )
            raise ValueError("Delivery OTP is blocked.")

        if not check_password(code, otp.code_hash):
            otp.attempts += 1

            if otp.attempts >= otp.max_attempts:
                otp.status = "BLOCKED"

            otp.save(
                update_fields=[
                    "attempts",
                    "status",
                    "updated_at",
                ]
            )

            raise ValueError("Invalid delivery OTP.")

        return otp