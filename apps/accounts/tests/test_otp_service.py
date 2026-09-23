from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.constants import OTPPurpose
from apps.accounts.models import OTPChallenge, User
from apps.accounts.services.otp import OTPService


@pytest.mark.django_db
class TestOTPService:

    def create_user(self):
        return User.objects.create_user(
            phone="01012345678",
            first_name="Test",
        )

    def test_generate_code_returns_six_digits(self):
        code = OTPService.generate_code()

        assert len(code) == 6
        assert code.isdigit()

    def test_create_challenge(self):
        user = self.create_user()

        challenge, code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        assert isinstance(challenge, OTPChallenge)
        assert len(code) == 6
        assert challenge.user == user
        assert challenge.purpose == OTPPurpose.LOGIN
        assert challenge.verified_at is None
        assert challenge.attempts == 0
        assert challenge.code_hash != code
        assert challenge.expires_at > timezone.now()

    def test_new_challenge_invalidates_previous_challenge(self):
        user = self.create_user()

        first_challenge, _ = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        second_challenge, _ = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        first_challenge.refresh_from_db()

        assert first_challenge.expires_at <= timezone.now()
        assert second_challenge.expires_at > timezone.now()

    def test_verify_correct_code(self):
        user = self.create_user()

        challenge, code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        result = OTPService.verify_challenge(
            challenge=challenge,
            code=code,
        )

        challenge.refresh_from_db()

        assert result is True
        assert challenge.verified_at is not None
        assert challenge.attempts == 1

    def test_verify_wrong_code(self):
        user = self.create_user()

        challenge, _ = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        result = OTPService.verify_challenge(
            challenge=challenge,
            code="000000",
        )

        challenge.refresh_from_db()

        assert result is False
        assert challenge.verified_at is None
        assert challenge.attempts == 1

    def test_expired_challenge_cannot_be_verified(self):
        user = self.create_user()

        challenge, code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        challenge.expires_at = timezone.now() - timedelta(minutes=1)
        challenge.save(update_fields=["expires_at"])

        result = OTPService.verify_challenge(
            challenge=challenge,
            code=code,
        )

        assert result is False

    def test_verified_challenge_cannot_be_reused(self):
        user = self.create_user()

        challenge, code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        first_result = OTPService.verify_challenge(
            challenge=challenge,
            code=code,
        )

        second_result = OTPService.verify_challenge(
            challenge=challenge,
            code=code,
        )

        assert first_result is True
        assert second_result is False

    def test_max_attempts(self):
        user = self.create_user()

        challenge, _ = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        for _ in range(challenge.max_attempts):
            result = OTPService.verify_challenge(
                challenge=challenge,
                code="000000",
            )

            assert result is False

        challenge.refresh_from_db()

        assert challenge.attempts == challenge.max_attempts

        result = OTPService.verify_challenge(
            challenge=challenge,
            code="000000",
        )

        assert result is False
        assert challenge.attempts == challenge.max_attempts