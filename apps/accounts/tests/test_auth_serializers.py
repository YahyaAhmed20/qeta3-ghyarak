import pytest

from apps.accounts.api.serializers import RequestLoginOTPSerializer


class TestRequestLoginOTPSerializer:

    def test_valid_egyptian_phone_is_normalized(self):
        serializer = RequestLoginOTPSerializer(
            data={"phone": "01012345678"}
        )

        assert serializer.is_valid()
        assert serializer.validated_data["phone"] == "+201012345678"

    def test_phone_with_spaces_is_normalized(self):
        serializer = RequestLoginOTPSerializer(
            data={"phone": "+20 101 234 5678"}
        )

        assert serializer.is_valid()
        assert serializer.validated_data["phone"] == "+201012345678"

    def test_invalid_phone_is_rejected(self):
        serializer = RequestLoginOTPSerializer(
            data={"phone": "12345"}
        )

        assert not serializer.is_valid()
        assert "phone" in serializer.errors

    def test_missing_phone_is_rejected(self):
        serializer = RequestLoginOTPSerializer(data={})

        assert not serializer.is_valid()
        assert "phone" in serializer.errors