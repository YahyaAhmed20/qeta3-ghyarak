import pytest

from apps.accounts.models import User
from apps.vehicles.models import (
    CustomerVehicle,
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)
from apps.vehicles.selectors.customer_vehicle import CustomerVehicleSelector


@pytest.fixture
def selector_customer(db):
    return User.objects.create_user(
        phone="01000000051",
        password="testpass123",
        role="CUSTOMER",
    )


@pytest.fixture
def selector_variant(db):
    make = VehicleMake.objects.create(
        name="Skoda",
        slug="skoda",
    )

    model = VehicleModel.objects.create(
        make=make,
        name="Octavia",
        slug="octavia",
    )

    generation = VehicleGeneration.objects.create(
        model=model,
        name="A7",
        slug="a7",
        year_from=2013,
        year_to=2019,
    )

    engine = VehicleEngine.objects.create(
        generation=generation,
        name="1.6 MPI",
        code="CWVA",
        displacement_cc=1598,
        fuel_type="PETROL",
        power_hp=110,
    )

    return VehicleVariant.objects.create(
        engine=engine,
        name="1.6 MPI Automatic",
        slug="1-6-mpi-automatic",
        transmission="AUTOMATIC",
        market="EGYPT",
    )


@pytest.mark.django_db
def test_get_customer_vehicles_returns_only_customer_vehicles(
    selector_customer,
    selector_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=selector_customer,
        vehicle_variant=selector_variant,
        nickname="My Car",
    )

    result = CustomerVehicleSelector.get_customer_vehicles(
        customer=selector_customer,
    )

    assert list(result) == [vehicle]


@pytest.mark.django_db
def test_get_customer_vehicles_returns_empty_queryset_for_customer_without_vehicles(
    selector_customer,
):
    result = CustomerVehicleSelector.get_customer_vehicles(
        customer=selector_customer,
    )

    assert result.exists() is False


@pytest.mark.django_db
def test_get_customer_vehicle_returns_owned_vehicle(
    selector_customer,
    selector_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=selector_customer,
        vehicle_variant=selector_variant,
        nickname="My Car",
    )

    result = CustomerVehicleSelector.get_customer_vehicle(
        customer=selector_customer,
        vehicle_id=vehicle.id,
    )

    assert result == vehicle


@pytest.mark.django_db
def test_get_customer_vehicle_returns_none_for_unknown_vehicle(
    selector_customer,
):
    result = CustomerVehicleSelector.get_customer_vehicle(
        customer=selector_customer,
        vehicle_id="00000000-0000-0000-0000-000000000000",
    )

    assert result is None


@pytest.mark.django_db
def test_get_customer_vehicle_does_not_return_another_customers_vehicle(
    selector_customer,
    selector_variant,
):
    another_customer = User.objects.create_user(
        phone="01000000052",
        password="testpass123",
        role="CUSTOMER",
    )

    vehicle = CustomerVehicle.objects.create(
        customer=another_customer,
        vehicle_variant=selector_variant,
        nickname="Other Car",
    )

    result = CustomerVehicleSelector.get_customer_vehicle(
        customer=selector_customer,
        vehicle_id=vehicle.id,
    )

    assert result is None


@pytest.mark.django_db
def test_get_default_vehicle_returns_default_vehicle(
    selector_customer,
    selector_variant,
):
    vehicle = CustomerVehicle.objects.create(
        customer=selector_customer,
        vehicle_variant=selector_variant,
        nickname="Default Car",
        is_default=True,
    )

    result = CustomerVehicleSelector.get_default_vehicle(
        customer=selector_customer,
    )

    assert result == vehicle


@pytest.mark.django_db
def test_get_default_vehicle_returns_none_when_no_default_exists(
    selector_customer,
    selector_variant,
):
    CustomerVehicle.objects.create(
        customer=selector_customer,
        vehicle_variant=selector_variant,
        nickname="Normal Car",
        is_default=False,
    )

    result = CustomerVehicleSelector.get_default_vehicle(
        customer=selector_customer,
    )

    assert result is None