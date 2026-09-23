import pytest
from django.db import IntegrityError

from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)


@pytest.mark.django_db
class TestVehicleVariant:

    def setup_vehicle_engine(self):
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
            name="A5",
            slug="a5",
            year_from=2004,
            year_to=2013,
        )

        engine = VehicleEngine.objects.create(
            generation=generation,
            name="1.6 MPI",
            code="BSE",
            displacement_cc=1595,
            fuel_type="PETROL",
            power_hp=102,
        )

        return generation, engine

    def test_create_vehicle_variant(self):
        generation, engine = self.setup_vehicle_engine()

        variant = VehicleVariant.objects.create(
            engine=engine,
            name="1.6 MPI Manual",
            slug="1-6-mpi-manual",
            transmission="MANUAL",
            market="EGYPT",
        )

        assert variant.engine == engine
        assert variant.engine.generation == generation
        assert variant.name == "1.6 MPI Manual"
        assert variant.transmission == "MANUAL"
        assert variant.market == "EGYPT"
        assert variant.is_active is True

    def test_vehicle_variant_str(self):
        _, engine = self.setup_vehicle_engine()

        variant = VehicleVariant.objects.create(
            engine=engine,
            name="1.6 MPI Manual",
            slug="1-6-mpi-manual",
        )

        assert str(variant) == f"{engine} - 1.6 MPI Manual"

    def test_same_variant_name_cannot_exist_under_same_engine(self):
        _, engine = self.setup_vehicle_engine()

        VehicleVariant.objects.create(
            engine=engine,
            name="1.6 MPI Manual",
            slug="manual",
        )

        with pytest.raises(IntegrityError):
            VehicleVariant.objects.create(
                engine=engine,
                name="1.6 MPI Manual",
                slug="manual-2",
            )

    def test_same_variant_slug_cannot_exist_under_same_engine(self):
        _, engine = self.setup_vehicle_engine()

        VehicleVariant.objects.create(
            engine=engine,
            name="Manual",
            slug="1-6-mpi",
        )

        with pytest.raises(IntegrityError):
            VehicleVariant.objects.create(
                engine=engine,
                name="Automatic",
                slug="1-6-mpi",
            )

    def test_same_variant_name_can_exist_under_different_engines(self):
        generation, engine_1 = self.setup_vehicle_engine()

        engine_2 = VehicleEngine.objects.create(
            generation=generation,
            name="2.0 FSI",
            code="BLX",
            displacement_cc=1984,
            fuel_type="PETROL",
            power_hp=150,
        )

        variant_1 = VehicleVariant.objects.create(
            engine=engine_1,
            name="Base",
            slug="base",
        )

        variant_2 = VehicleVariant.objects.create(
            engine=engine_2,
            name="Base",
            slug="base",
        )

        assert variant_1.name == variant_2.name
        assert variant_1.engine != variant_2.engine

    def test_deleting_engine_is_protected(self):
        _, engine = self.setup_vehicle_engine()

        VehicleVariant.objects.create(
            engine=engine,
            name="1.6 MPI Manual",
            slug="1-6-mpi-manual",
        )

        with pytest.raises(Exception):
            engine.delete()