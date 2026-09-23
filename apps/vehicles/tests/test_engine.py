import pytest

from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
)


@pytest.mark.django_db
class TestVehicleEngine:

    def setup_method(self):
        self.make = VehicleMake.objects.create(
            name="Skoda",
            slug="skoda",
        )

        self.model = VehicleModel.objects.create(
            make=self.make,
            name="Octavia",
            slug="octavia",
        )

        self.generation = VehicleGeneration.objects.create(
            model=self.model,
            name="A7",
            slug="a7",
            year_from=2013,
            year_to=2019,
        )

    def test_create_vehicle_engine(self):
        engine = VehicleEngine.objects.create(
            generation=self.generation,
            name="1.6 MPI",
            code="BSE",
            displacement_cc=1595,
            fuel_type="PETROL",
            power_hp=102,
        )

        assert engine.id is not None
        assert engine.generation == self.generation
        assert engine.name == "1.6 MPI"
        assert engine.code == "BSE"
        assert engine.displacement_cc == 1595
        assert engine.fuel_type == "PETROL"
        assert engine.power_hp == 102
        assert engine.is_active is True

    def test_same_engine_name_cannot_exist_under_same_generation(self):
        VehicleEngine.objects.create(
            generation=self.generation,
            name="1.6 MPI",
            code="BSE",
        )

        with pytest.raises(Exception):
            VehicleEngine.objects.create(
                generation=self.generation,
                name="1.6 MPI",
                code="BSE-2",
            )

    def test_same_engine_can_exist_under_different_generations(self):
        another_generation = VehicleGeneration.objects.create(
            model=self.model,
            name="A8",
            slug="a8",
            year_from=2020,
            year_to=2024,
        )

        first_engine = VehicleEngine.objects.create(
            generation=self.generation,
            name="1.6 MPI",
            code="BSE",
        )

        second_engine = VehicleEngine.objects.create(
            generation=another_generation,
            name="1.6 MPI",
            code="BSE",
        )

        assert first_engine.id != second_engine.id
        assert first_engine.generation == self.generation
        assert second_engine.generation == another_generation

    def test_deleting_generation_is_protected(self):
        VehicleEngine.objects.create(
            generation=self.generation,
            name="1.6 MPI",
            code="BSE",
        )

        with pytest.raises(Exception):
            self.generation.delete()