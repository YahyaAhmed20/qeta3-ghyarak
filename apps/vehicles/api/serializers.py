from rest_framework import serializers

from apps.common.normalizers import normalize_vin
from apps.vehicles.models import CustomerVehicle, VehicleVariant


class VehicleVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleVariant
        fields = [
            "id",
            "name",
            "slug",
            "transmission",
            "market",
        ]
        read_only_fields = fields


class CustomerVehicleSerializer(serializers.ModelSerializer):
    vehicle_variant = VehicleVariantSerializer(read_only=True)

    class Meta:
        model = CustomerVehicle
        fields = [
            "id",
            "vehicle_variant",
            "nickname",
            "plate_number",
            "vin",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "vehicle_variant",
            "is_default",
            "created_at",
            "updated_at",
        ]


class CustomerVehicleCreateSerializer(serializers.Serializer):
    vehicle_variant = serializers.PrimaryKeyRelatedField(
        queryset=VehicleVariant.objects.filter(is_active=True),
    )
    nickname = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    plate_number = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
    )
    vin = serializers.CharField(
        max_length=17,
        required=False,
        allow_blank=True,
    )

    def validate_vin(self, value):
        if not value:
            return value

        normalized_vin = normalize_vin(value)

        if len(normalized_vin) != 17:
            raise serializers.ValidationError(
                "VIN must contain exactly 17 characters."
            )

        return normalized_vin


class CustomerVehicleUpdateSerializer(serializers.Serializer):
    nickname = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    plate_number = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
    )
    vin = serializers.CharField(
        max_length=17,
        required=False,
        allow_blank=True,
    )
    vehicle_variant = serializers.PrimaryKeyRelatedField(
        queryset=VehicleVariant.objects.all(),
        required=False,
    )

    def validate(self, attrs):
        if "vehicle_variant" in attrs:
            raise serializers.ValidationError(
                {
                    "vehicle_variant": (
                        "Vehicle variant cannot be changed."
                    )
                }
            )

        return attrs

    def validate_vin(self, value):
        if not value:
            return value

        normalized_vin = normalize_vin(value)

        if len(normalized_vin) != 17:
            raise serializers.ValidationError(
                "VIN must contain exactly 17 characters."
            )

        return normalized_vin