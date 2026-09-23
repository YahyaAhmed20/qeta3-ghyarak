from django.db import transaction

from apps.accounts.models.otp import OTPChallenge

from ..constants import OTPPurpose, UserStatus
from ..models import User
from .otp import OTPService
from rest_framework_simplejwt.tokens import RefreshToken
from apps.common.phone import normalize_egyptian_phone
from django.utils import timezone
class AuthService:

    @staticmethod
    @transaction.atomic
    def request_login_otp(phone: str):
        """
        Find or create a customer and create a LOGIN OTP.
        """

        phone = normalize_egyptian_phone(phone)

        user = User.objects.filter(phone=phone).first()

        if user is None:
            user = User.objects.create_user(
                phone=phone,
                first_name="",
            )

        if not user.is_active or user.status != UserStatus.ACTIVE:
            raise ValueError("User account is inactive.")

        challenge, code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        return user, challenge, code
    
    
    @staticmethod
    @transaction.atomic
    def verify_phone_otp(challenge_id, code: str):
        challenge = (
            OTPChallenge.objects
            .select_for_update()
            .select_related("user")
            .get(
                id=challenge_id,
                purpose=OTPPurpose.PHONE_VERIFICATION,
            )
        )

        if not OTPService.verify_challenge(
            challenge=challenge,
            code=code,
        ):
            raise ValueError("Invalid or expired OTP.")

        user = challenge.user

        if not user.is_verified:
            user.is_verified = True
            user.save(
                update_fields=[
                    "is_verified",
                    "updated_at",
                ]
            )

        return user
    
    @staticmethod
    @transaction.atomic
    def verify_login_otp(challenge_id, code: str):
        challenge = (
            OTPChallenge.objects
            .select_for_update()
            .select_related("user")
            .filter(
                id=challenge_id,
                purpose=OTPPurpose.LOGIN,
            )
            .first()
        )

        if challenge is None:
            raise ValueError("Invalid or expired OTP.")

        if not OTPService.verify_challenge(
            challenge=challenge,
            code=code,
        ):
            raise ValueError("Invalid or expired OTP.")

        user = challenge.user

        if not user.is_active or user.status != UserStatus.ACTIVE:
            raise ValueError("User account is inactive.")

        if not user.is_verified:
            raise ValueError("Phone number is not verified.")

        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }