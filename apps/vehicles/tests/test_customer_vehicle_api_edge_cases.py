import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.vehicles.models import (
    CustomerVehicle,
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)

User = get_user_model()


@pytest.mark.django_db
class TestCustomerVehicleAPIEdgeCases:

    def setup_method(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            phone="01000000000",
            password="TestPassword123",
        )

        self.other_user = User.objects.create_user(
            phone="01111111111",
            password="TestPassword123",
        )

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

        self.variant = VehicleVariant.objects.create(
            engine=engine,
            name="1.6 MPI Automatic",
            slug="1-6-mpi-automatic",
            transmission="AUTOMATIC",
            market="EGYPT",
            is_active=True,
        )

        self.inactive_variant = VehicleVariant.objects.create(
            engine=engine,
            name="1.6 MPI Manual",
            slug="1-6-mpi-manual",
            transmission="MANUAL",
            market="EGYPT",
            is_active=False,
        )

        self.client.force_authenticate(user=self.user)

    def test_add_vehicle_requires_vehicle_variant(self):
        response = self.client.post(
            "/api/v1/vehicles/",
            {
                "nickname": "My Car",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_add_vehicle_with_unknown_variant_returns_400(self):
        response = self.client.post(
            "/api/v1/vehicles/",
            {
                "vehicle_variant": "00000000-0000-0000-0000-000000000000",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_add_inactive_variant_returns_400(self):
        response = self.client.post(
            "/api/v1/vehicles/",
            {
                "vehicle_variant": str(self.inactive_variant.id),
            },
            format="json",
        )

        assert response.status_code == 400

    def test_add_duplicate_vehicle_returns_400(self):
        CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="Existing Car",
        )

        response = self.client.post(
            "/api/v1/vehicles/",
            {
                "vehicle_variant": str(self.variant.id),
                "nickname": "Duplicate Car",
            },
            format="json",
        )

        assert response.status_code == 400

        assert CustomerVehicle.objects.filter(
            customer=self.user,
            vehicle_variant=self.variant,
        ).count() == 1

    def test_add_vehicle_with_invalid_vin_returns_400(self):
        response = self.client.post(
            "/api/v1/vehicles/",
            {
                "vehicle_variant": str(self.variant.id),
                "vin": "INVALID-VIN",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_add_vehicle_normalizes_vin(self):
        vin = " tmb12345678901234 "

        response = self.client.post(
            "/api/v1/vehicles/",
            {
                "vehicle_variant": str(self.variant.id),
                "vin": vin,
            },
            format="json",
        )

        assert response.status_code == 201

        vehicle = CustomerVehicle.objects.get(
            customer=self.user,
            vehicle_variant=self.variant,
        )

        assert vehicle.vin == "TMB12345678901234"

    def test_customer_cannot_be_changed(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="My Car",
        )

        response = self.client.patch(
            f"/api/v1/vehicles/{vehicle.id}/",
            {
                "customer": str(self.other_user.id),
                "nickname": "Updated",
            },
            format="json",
        )

        assert response.status_code == 200

        vehicle.refresh_from_db()

        assert vehicle.customer == self.user
        assert vehicle.nickname == "Updated"

    def test_vehicle_variant_cannot_be_changed(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="My Car",
        )

        response = self.client.patch(
            f"/api/v1/vehicles/{vehicle.id}/",
            {
                "vehicle_variant": str(self.inactive_variant.id),
            },
            format="json",
        )

        assert response.status_code == 400

        vehicle.refresh_from_db()

        assert vehicle.vehicle_variant == self.variant

    def test_set_default_unknown_vehicle_returns_404(self):
        response = self.client.patch(
            "/api/v1/vehicles/"
            "00000000-0000-0000-0000-000000000000/"
            "set-default/",
            {},
            format="json",
        )

        assert response.status_code == 404

    def test_set_default_another_customer_vehicle_returns_404(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.other_user,
            vehicle_variant=self.variant,
            nickname="Other Car",
        )

        response = self.client.patch(
            f"/api/v1/vehicles/{vehicle.id}/set-default/",
            {},
            format="json",
        )

        assert response.status_code == 404

        vehicle.refresh_from_db()

        assert vehicle.is_default is False

    def test_delete_default_vehicle_promotes_another_vehicle(self):
        first = CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="First Car",
            is_default=True,
        )

        engine = VehicleEngine.objects.create(
            generation=self.variant.engine.generation,
            name="2.0 FSI",
            code="BLX",
            displacement_cc=1984,
            fuel_type="PETROL",
            power_hp=150,
        )

        second_variant = VehicleVariant.objects.create(
            engine=engine,
            name="2.0 FSI Automatic",
            slug="2-0-fsi-automatic",
            is_active=True,
        )

        second = CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=second_variant,
            nickname="Second Car",
            is_default=False,
        )

        response = self.client.delete(
            f"/api/v1/vehicles/{first.id}/"
        )

        assert response.status_code == 204

        second.refresh_from_db()

        assert second.is_default is True