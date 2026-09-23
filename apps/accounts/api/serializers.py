from rest_framework import serializers

from apps.accounts.models import User
from apps.common.phone import normalize_egyptian_phone


class RequestLoginOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(
        max_length=20,
        write_only=True,
    )

    def validate_phone(self, value):
        try:
            return normalize_egyptian_phone(value)
        except ValueError:
            raise serializers.ValidationError(
                "Invalid Egyptian mobile number."
            )
            
class VerifyLoginOTPSerializer(serializers.Serializer):
    challenge_id = serializers.UUIDField()
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        write_only=True,
    )


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_verified",
        ]
        read_only_fields = fields