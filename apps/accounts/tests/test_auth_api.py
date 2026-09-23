import pytest

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.constants import OTPPurpose
from apps.accounts.models import OTPChallenge, User
from apps.accounts.services.otp import OTPService


@pytest.mark.django_db
class TestRequestLoginOTPAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_request_login_otp_success(self):
        response = self.client.post(
            "/api/v1/auth/login/request-otp/",
            {
                "phone": "01012345678",
            },
            format="json",
        )

        assert response.status_code == 200

        data = response.json()

        assert "challenge_id" in data
        assert data["message"] == "OTP sent successfully."

        user = User.objects.get(
            phone="+201012345678",
        )

        assert user.is_active is True

        challenge = OTPChallenge.objects.get(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        assert str(challenge.id) == data["challenge_id"]

        # OTP must never be exposed through the API.
        assert "code" not in data
        assert "otp" not in data

    def test_request_login_otp_invalid_phone(self):
        response = self.client.post(
            "/api/v1/auth/login/request-otp/",
            {
                "phone": "12345",
            },
            format="json",
        )

        assert response.status_code == 400

        data = response.json()

        assert "phone" in data

    def test_request_login_otp_missing_phone(self):
        response = self.client.post(
            "/api/v1/auth/login/request-otp/",
            {},
            format="json",
        )

        assert response.status_code == 400

        data = response.json()

        assert "phone" in data


@pytest.mark.django_db
class TestVerifyLoginOTPAPI:

    def setup_method(self):
        self.client = APIClient()

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

        response = self.client.post(
            "/api/v1/auth/login/verify-otp/",
            {
                "challenge_id": str(challenge.id),
                "code": code,
            },
            format="json",
        )

        assert response.status_code == 200

        data = response.json()

        assert "access" in data
        assert "refresh" in data

        assert data["access"]
        assert data["refresh"]

        challenge.refresh_from_db()

        assert challenge.verified_at is not None

    def test_verify_login_otp_with_wrong_code_is_rejected(self):
        user = User.objects.create_user(
            phone="+201012345678",
            first_name="Yahya",
            is_verified=True,
        )

        challenge, _code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        response = self.client.post(
            "/api/v1/auth/login/verify-otp/",
            {
                "challenge_id": str(challenge.id),
                "code": "000000",
            },
            format="json",
        )

        assert response.status_code == 400

        challenge.refresh_from_db()

        assert challenge.verified_at is None

    def test_verify_login_otp_requires_valid_challenge_id(self):
        response = self.client.post(
            "/api/v1/auth/login/verify-otp/",
            {
                "challenge_id": "00000000-0000-0000-0000-000000000000",
                "code": "123456",
            },
            format="json",
        )

        assert response.status_code == 400

        data = response.json()

        assert data["detail"] == "Invalid or expired OTP."

    def test_access_token_can_authenticate_me_endpoint(self):
        user = User.objects.create_user(
            phone="+201012345678",
            first_name="Yahya",
            last_name="Ahmed",
            is_verified=True,
        )

        challenge, code = OTPService.create_challenge(
            user=user,
            purpose=OTPPurpose.LOGIN,
        )

        login_response = self.client.post(
            "/api/v1/auth/login/verify-otp/",
            {
                "challenge_id": str(challenge.id),
                "code": code,
            },
            format="json",
        )

        assert login_response.status_code == 200

        tokens = login_response.json()

        access_token = tokens["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        response = self.client.get(
            "/api/v1/auth/me/",
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(user.id)
        assert data["phone"] == "+201012345678"
        assert data["first_name"] == "Yahya"
        assert data["last_name"] == "Ahmed"
        assert data["is_verified"] is True

    def test_me_requires_authentication(self):
        response = self.client.get(
            "/api/v1/auth/me/",
        )

        assert response.status_code == 401