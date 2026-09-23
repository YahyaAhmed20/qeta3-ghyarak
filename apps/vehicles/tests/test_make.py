import pytest

from apps.vehicles.models import VehicleMake


@pytest.mark.django_db
class TestVehicleMake:

    def test_create_vehicle_make(self):
        make = VehicleMake.objects.create(
            name="Skoda",
            slug="skoda",
        )

        assert make.id is not None
        assert make.name == "Skoda"
        assert make.slug == "skoda"
        assert make.is_active is True

    def test_vehicle_make_name_must_be_unique(self):
        VehicleMake.objects.create(
            name="Skoda",
            slug="skoda",
        )

        with pytest.raises(Exception):
            VehicleMake.objects.create(
                name="Skoda",
                slug="skoda-2",
            )