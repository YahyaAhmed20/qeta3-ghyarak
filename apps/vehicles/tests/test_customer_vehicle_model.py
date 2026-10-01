import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.accounts.models import User
from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)





@pytest.mark.django_db
def test_customer_vehicle_can_be_created(customer, vehicle_variant):
    from apps.vehicles.models import CustomerVehicle

    customer_vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
        nickname="My Octavia",
        plate_number="س ص 1234",
        vin="TMB12345678901234",
    )

    assert customer_vehicle.customer == customer
    assert customer_vehicle.vehicle_variant == vehicle_variant
    assert customer_vehicle.nickname == "My Octavia"
    assert customer_vehicle.plate_number == "س ص 1234"
    assert customer_vehicle.vin == "TMB12345678901234"


@pytest.mark.django_db
def test_customer_vehicle_has_uuid_primary_key(customer, vehicle_variant):
    from apps.vehicles.models import CustomerVehicle

    customer_vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    assert customer_vehicle.id is not None
    assert customer_vehicle.id.version == 4


@pytest.mark.django_db
def test_customer_vehicle_is_not_default_by_default(customer, vehicle_variant):
    from apps.vehicles.models import CustomerVehicle

    customer_vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    assert customer_vehicle.is_default is False


@pytest.mark.django_db
def test_customer_vehicle_optional_fields_can_be_blank(
    customer,
    vehicle_variant,
):
    from apps.vehicles.models import CustomerVehicle

    customer_vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    assert customer_vehicle.nickname == ""
    assert customer_vehicle.plate_number == ""
    assert customer_vehicle.vin == ""


@pytest.mark.django_db
def test_customer_vehicle_str_returns_nickname(
    customer,
    vehicle_variant,
):
    from apps.vehicles.models import CustomerVehicle

    customer_vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
        nickname="My Car",
    )

    assert str(customer_vehicle) == "My Car"


@pytest.mark.django_db
def test_customer_vehicle_requires_customer(vehicle_variant):
    from apps.vehicles.models import CustomerVehicle

    with pytest.raises(IntegrityError):
        CustomerVehicle.objects.create(
            customer=None,
            vehicle_variant=vehicle_variant,
        )


@pytest.mark.django_db
def test_customer_vehicle_requires_vehicle_variant(customer):
    from apps.vehicles.models import CustomerVehicle

    with pytest.raises(IntegrityError):
        CustomerVehicle.objects.create(
            customer=customer,
            vehicle_variant=None,
        )


@pytest.mark.django_db
def test_customer_vehicle_normalizes_vin(
    customer,
    vehicle_variant,
):
    from apps.vehicles.models import CustomerVehicle

    customer_vehicle = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
        vin="tmb12345678901234",
    )

    customer_vehicle.full_clean()

    assert customer_vehicle.vin == "TMB12345678901234"


@pytest.mark.django_db
def test_customer_vehicle_rejects_invalid_vin(
    customer,
    vehicle_variant,
):
    from apps.vehicles.models import CustomerVehicle

    customer_vehicle = CustomerVehicle(
        customer=customer,
        vehicle_variant=vehicle_variant,
        vin="ABC123",
    )

    with pytest.raises(ValidationError):
        customer_vehicle.full_clean()