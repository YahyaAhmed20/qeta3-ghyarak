import pytest
from django.utils import timezone

from apps.accounts.constants import OTPPurpose, UserStatus
from apps.accounts.models import OTPChallenge, User
from apps.accounts.services.auth import AuthService
from apps.accounts.services.otp import OTPService


@pytest.mark.django_db
class TestAuthService:

    def test_request_login_otp_creates_new_customer(self):
        user, challenge, code = AuthService.request_login_otp(
            "01012345678"
        )

        assert user.phone == "+201012345678"
        assert user.role == "CUSTOMER"
        assert user.is_active is True
        assert challenge.user == user
        assert challenge.purpose == OTPPurpose.LOGIN
        assert len(code) == 6
        assert User.objects.count() == 1

    def test_request_login_otp_normalizes_existing_user(self):
        user = User.objects.create_user(
            phone="+201012345678",
            first_name="Test",
        )

        returned_user, challenge, code = AuthService.request_login_otp(
            "01012345678"
        )

        assert returned_user.id == user.id
        assert User.objects.count() == 1
        assert challenge.user == user
        assert len(code) == 6

    def test_request_login_otp_invalidates_previous_otp(self):
        user, first_challenge, _ = AuthService.request_login_otp(
            "01012345678"
        )

        _, second_challenge, _ = AuthService.request_login_otp(
            "01012345678"
        )

        first_challenge.refresh_from_db()

        assert first_challenge.expires_at <= timezone.now()
        assert second_challenge.expires_at > timezone.now()

    def test_inactive_user_cannot_request_login_otp(self):
        user = User.objects.create_user(
            phone="01012345678",
            first_name="Test",
            status=UserStatus.INACTIVE,
        )

        with pytest.raises(ValueError, match="inactive"):
            AuthService.request_login_otp(
                "01012345678"
            )

        assert OTPChallenge.objects.count() == 0
        
        
    def test_verify_phone_otp_marks_user_verified(self):
        user = User.objects.create_user(
            phone="01012345678",
            first_name="Test",
        )

        challenge, code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.PHONE_VERIFICATION,
        )

        assert user.is_verified is False

        returned_user = AuthService.verify_phone_otp(
            challenge_id=challenge.id,
            code=code,
        )

        user.refresh_from_db()

        assert returned_user.id == user.id
        assert user.is_verified is True

        challenge.refresh_from_db()

        assert challenge.verified_at is not None
        
        
    def test_verify_phone_otp_with_wrong_code_does_not_verify_user(self):
        user = User.objects.create_user(
            phone="01012345678",
            first_name="Test",
        )

        challenge, _ = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.PHONE_VERIFICATION,
        )

        with pytest.raises(ValueError, match="Invalid or expired OTP"):
            AuthService.verify_phone_otp(
                challenge_id=challenge.id,
                code="000000",
            )

        user.refresh_from_db()

        assert user.is_verified is False
        
    def test_verify_login_otp_returns_jwt_tokens(self):
        user = User.objects.create_user(
            phone="+201012345678",
            first_name="Yahya",
            is_verified=True,
        )

        challenge, code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        tokens = AuthService.verify_login_otp(
            challenge_id=challenge.id,
            code=code,
        )

        assert "access" in tokens
        assert "refresh" in tokens
        assert tokens["access"]
        assert tokens["refresh"]

        challenge.refresh_from_db()

        assert challenge.verified_at is not None