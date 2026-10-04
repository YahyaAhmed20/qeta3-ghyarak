from rest_framework import serializers

from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)


class VehicleMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleMake
        fields = [
            "id",
            "name",
            "slug",
        ]
        read_only_fields = fields


class VehicleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleModel
        fields = [
            "id",
            "name",
            "slug",
        ]
        read_only_fields = fields


class VehicleGenerationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleGeneration
        fields = [
            "id",
            "name",
            "slug",
            "year_from",
            "year_to",
        ]
        read_only_fields = fields


class VehicleEngineSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleEngine
        fields = [
            "id",
            "name",
            "code",
            "displacement_cc",
            "fuel_type",
            "power_hp",
        ]
        read_only_fields = fields


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