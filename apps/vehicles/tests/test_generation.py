import pytest

from apps.vehicles.models import (
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
)


@pytest.mark.django_db
class TestVehicleGeneration:

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

    def test_create_vehicle_generation(self):
        generation = VehicleGeneration.objects.create(
            model=self.model,
            name="A7",
            slug="a7",
            year_from=2013,
            year_to=2019,
        )

        assert generation.id is not None
        assert generation.model == self.model
        assert generation.name == "A7"
        assert generation.slug == "a7"
        assert generation.year_from == 2013
        assert generation.year_to == 2019
        assert generation.is_active is True

    def test_same_generation_name_cannot_exist_under_same_model(self):
        VehicleGeneration.objects.create(
            model=self.model,
            name="A7",
            slug="a7",
        )

        with pytest.raises(Exception):
            VehicleGeneration.objects.create(
                model=self.model,
                name="A7",
                slug="a7-2",
            )

    def test_same_generation_can_exist_under_different_models(self):
        another_model = VehicleModel.objects.create(
            make=self.make,
            name="Superb",
            slug="superb",
        )

        octavia_generation = VehicleGeneration.objects.create(
            model=self.model,
            name="A7",
            slug="a7",
        )

        superb_generation = VehicleGeneration.objects.create(
            model=another_model,
            name="A7",
            slug="a7",
        )

        assert octavia_generation.id != superb_generation.id
        assert octavia_generation.model == self.model
        assert superb_generation.model == another_model

    def test_deleting_model_is_protected(self):
        VehicleGeneration.objects.create(
            model=self.model,
            name="A7",
            slug="a7",
        )

        with pytest.raises(Exception):
            self.model.delete()