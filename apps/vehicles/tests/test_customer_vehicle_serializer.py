import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from apps.vehicles.api.serializers import (
    CustomerVehicleCreateSerializer,
    CustomerVehicleSerializer,
    CustomerVehicleUpdateSerializer,
)
from apps.vehicles.models import CustomerVehicle


@pytest.mark.django_db
def test_customer_vehicle_serializer_returns_expected_fields(
    customer,
    vehicle_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
        nickname="My Octavia",
        plate_number="س ص 1234",
        vin="TMB12345678901234",
        is_default=True,
    )

    serializer = CustomerVehicleSerializer(vehicle)

    assert serializer.data["id"] == str(vehicle.id)
    assert serializer.data["nickname"] == "My Octavia"
    assert serializer.data["plate_number"] == "س ص 1234"
    assert serializer.data["vin"] == "TMB12345678901234"
    assert serializer.data["is_default"] is True


@pytest.mark.django_db
def test_customer_vehicle_serializer_includes_vehicle_information(
    customer,
    vehicle_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    serializer = CustomerVehicleSerializer(vehicle)

    data = serializer.data

    assert "vehicle_variant" in data
    assert data["vehicle_variant"]["id"] == str(vehicle_variant.id)
    assert data["vehicle_variant"]["name"] == vehicle_variant.name


@pytest.mark.django_db
def test_customer_vehicle_serializer_does_not_expose_customer(
    customer,
    vehicle_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    serializer = CustomerVehicleSerializer(vehicle)

    assert "customer" not in serializer.data


@pytest.mark.django_db
def test_create_serializer_accepts_allowed_fields(
    customer,
    vehicle_variant,
):
    serializer = CustomerVehicleCreateSerializer(
        data={
            "vehicle_variant": str(vehicle_variant.id),
            "nickname": "My Octavia",
            "plate_number": "س ص 1234",
            "vin": "TMB12345678901234",
        }
    )

    assert serializer.is_valid(), serializer.errors

    assert serializer.validated_data["vehicle_variant"] == vehicle_variant
    assert serializer.validated_data["nickname"] == "My Octavia"
    assert serializer.validated_data["plate_number"] == "س ص 1234"


@pytest.mark.django_db
def test_create_serializer_does_not_accept_customer(
    customer,
    vehicle_variant,
):
    serializer = CustomerVehicleCreateSerializer(
        data={
            "customer": str(customer.id),
            "vehicle_variant": str(vehicle_variant.id),
            "nickname": "My Octavia",
        }
    )

    assert serializer.is_valid(), serializer.errors
    assert "customer" not in serializer.validated_data


@pytest.mark.django_db
def test_create_serializer_rejects_invalid_vin(
    vehicle_variant,
):
    serializer = CustomerVehicleCreateSerializer(
        data={
            "vehicle_variant": str(vehicle_variant.id),
            "vin": "INVALID",
        }
    )

    assert not serializer.is_valid()
    assert "vin" in serializer.errors


@pytest.mark.django_db
def test_update_serializer_accepts_partial_fields(
    customer,
    vehicle_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
        nickname="Old Name",
    )

    serializer = CustomerVehicleUpdateSerializer(
        vehicle,
        data={
            "nickname": "New Name",
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["nickname"] == "New Name"


@pytest.mark.django_db
def test_update_serializer_rejects_vehicle_variant_change(
    customer,
    vehicle_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    serializer = CustomerVehicleUpdateSerializer(
        vehicle,
        data={
            "vehicle_variant": str(vehicle_variant.id),
        },
        partial=True,
    )

    assert not serializer.is_valid()
    assert "vehicle_variant" in serializer.errors
    assert (
        str(serializer.errors["vehicle_variant"][0])
        == "Vehicle variant cannot be changed."
    )


@pytest.mark.django_db
def test_update_serializer_does_not_allow_customer_change(
    customer,
    vehicle_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    serializer = CustomerVehicleUpdateSerializer(
        vehicle,
        data={
            "customer": str(customer.id),
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    assert "customer" not in serializer.validated_data