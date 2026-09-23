import pytest

from apps.vehicles.models import VehicleMake, VehicleModel


@pytest.mark.django_db
class TestVehicleModel:

    def test_create_vehicle_model(self):
        make = VehicleMake.objects.create(
            name="Skoda",
            slug="skoda",
        )

        vehicle_model = VehicleModel.objects.create(
            make=make,
            name="Octavia",
            slug="octavia",
        )

        assert vehicle_model.id is not None
        assert vehicle_model.make == make
        assert vehicle_model.name == "Octavia"
        assert vehicle_model.slug == "octavia"
        assert vehicle_model.is_active is True

    def test_same_model_name_cannot_exist_under_same_make(self):
        make = VehicleMake.objects.create(
            name="Skoda",
            slug="skoda",
        )

        VehicleModel.objects.create(
            make=make,
            name="Octavia",
            slug="octavia",
        )

        with pytest.raises(Exception):
            VehicleModel.objects.create(
                make=make,
                name="Octavia",
                slug="octavia-2",
            )

    def test_same_model_can_exist_under_different_makes(self):
        skoda = VehicleMake.objects.create(
            name="Skoda",
            slug="skoda",
        )

        toyota = VehicleMake.objects.create(
            name="Toyota",
            slug="toyota",
        )

        skoda_model = VehicleModel.objects.create(
            make=skoda,
            name="Corolla",
            slug="corolla",
        )

        toyota_model = VehicleModel.objects.create(
            make=toyota,
            name="Corolla",
            slug="corolla",
        )

        assert skoda_model.id != toyota_model.id
        assert skoda_model.make == skoda
        assert toyota_model.make == toyota

    def test_deleting_make_is_protected(self):
        make = VehicleMake.objects.create(
            name="Skoda",
            slug="skoda",
        )

        VehicleModel.objects.create(
            make=make,
            name="Octavia",
            slug="octavia",
        )

        with pytest.raises(Exception):
            make.delete()