import pytest

from apps.accounts.models import User
from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        phone="01000000001",
        password="testpass123",
    )


@pytest.fixture
def vehicle_variant(db):
    make = VehicleMake.objects.create(
        name="Skoda",
        slug="skoda",
    )

    vehicle_model = VehicleModel.objects.create(
        make=make,
        name="Octavia",
        slug="octavia",
    )

    generation = VehicleGeneration.objects.create(
        model=vehicle_model,
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
        fuel_type="Petrol",
        power_hp=110,
    )

    return VehicleVariant.objects.create(
        engine=engine,
        name="1.6 MPI Automatic",
        slug="1-6-mpi-automatic",
        transmission="Automatic",
        market="EU",
    )