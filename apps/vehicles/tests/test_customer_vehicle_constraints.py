import pytest
from django.db import IntegrityError, transaction

from apps.vehicles.models import CustomerVehicle


@pytest.mark.django_db
def test_customer_cannot_add_same_vehicle_variant_twice(
    customer,
    vehicle_variant,
):
    CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CustomerVehicle.objects.create(
                customer=customer,
                vehicle_variant=vehicle_variant,
            )


@pytest.mark.django_db
def test_customer_cannot_have_two_default_vehicles(
    customer,
    vehicle_variant,
):
    first = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
        nickname="First",
        is_default=True,
    )

    # Create a different variant under the same vehicle hierarchy.
    second_variant = type(vehicle_variant).objects.create(
        engine=vehicle_variant.engine,
        name="1.6 MPI Manual",
        slug="1-6-mpi-manual",
        transmission="Manual",
        market="EU",
    )

    assert first.is_default is True

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CustomerVehicle.objects.create(
                customer=customer,
                vehicle_variant=second_variant,
                nickname="Second",
                is_default=True,
            )


@pytest.mark.django_db
def test_different_customers_can_use_same_vehicle_variant(
    customer,
    vehicle_variant,
):
    from apps.accounts.models import User

    second_customer = User.objects.create_user(
        phone="01000000002",
        password="testpass123",
    )

    first = CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    second = CustomerVehicle.objects.create(
        customer=second_customer,
        vehicle_variant=vehicle_variant,
    )

    assert first.vehicle_variant == second.vehicle_variant
    assert first.customer != second.customer


@pytest.mark.django_db
def test_vehicle_variant_cannot_be_deleted_when_used_by_customer(
    customer,
    vehicle_variant,
):
    CustomerVehicle.objects.create(
        customer=customer,
        vehicle_variant=vehicle_variant,
    )

    with pytest.raises(Exception):
        vehicle_variant.delete()