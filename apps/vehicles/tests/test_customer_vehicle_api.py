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
class TestCustomerVehicleAPI:

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
        )

        self.client.force_authenticate(user=self.user)

    def test_add_vehicle(self):
        response = self.client.post(
            "/api/v1/vehicles/",
            {
                "vehicle_variant": str(self.variant.id),
                "nickname": "My Octavia",
                "plate_number": "س ص 1234",
                "vin": "TMB12345678901234",
            },
            format="json",
        )

        assert response.status_code == 201

        assert CustomerVehicle.objects.filter(
            customer=self.user,
            vehicle_variant=self.variant,
        ).exists()

        vehicle = CustomerVehicle.objects.get(
            customer=self.user,
            vehicle_variant=self.variant,
        )

        assert vehicle.nickname == "My Octavia"
        assert vehicle.is_default is True

    def test_list_vehicles(self):
        CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="My Octavia",
        )

        response = self.client.get(
            "/api/v1/vehicles/"
        )

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_list_vehicles_returns_only_current_customer_vehicles(self):
        CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="My Car",
        )

        CustomerVehicle.objects.create(
            customer=self.other_user,
            vehicle_variant=self.variant,
            nickname="Other Car",
        )

        response = self.client.get(
            "/api/v1/vehicles/"
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["nickname"] == "My Car"

    def test_get_vehicle_detail(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="My Octavia",
        )

        response = self.client.get(
            f"/api/v1/vehicles/{vehicle.id}/"
        )

        assert response.status_code == 200
        assert response.data["id"] == str(vehicle.id)
        assert response.data["nickname"] == "My Octavia"

    def test_customer_cannot_access_another_customer_vehicle(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.other_user,
            vehicle_variant=self.variant,
            nickname="Other Car",
        )

        response = self.client.get(
            f"/api/v1/vehicles/{vehicle.id}/"
        )

        assert response.status_code == 404

    def test_update_vehicle(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="Old Name",
        )

        response = self.client.patch(
            f"/api/v1/vehicles/{vehicle.id}/",
            {
                "nickname": "New Name",
                "plate_number": "XYZ 789",
            },
            format="json",
        )

        assert response.status_code == 200

        vehicle.refresh_from_db()

        assert vehicle.nickname == "New Name"
        assert vehicle.plate_number == "XYZ 789"

    def test_customer_cannot_update_another_customer_vehicle(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.other_user,
            vehicle_variant=self.variant,
            nickname="Other Car",
        )

        response = self.client.patch(
            f"/api/v1/vehicles/{vehicle.id}/",
            {
                "nickname": "Hacked",
            },
            format="json",
        )

        assert response.status_code == 404

        vehicle.refresh_from_db()

        assert vehicle.nickname == "Other Car"

    def test_delete_vehicle(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=self.variant,
            nickname="My Car",
        )

        response = self.client.delete(
            f"/api/v1/vehicles/{vehicle.id}/"
        )

        assert response.status_code == 204

        assert not CustomerVehicle.objects.filter(
            id=vehicle.id
        ).exists()

    def test_customer_cannot_delete_another_customer_vehicle(self):
        vehicle = CustomerVehicle.objects.create(
            customer=self.other_user,
            vehicle_variant=self.variant,
            nickname="Other Car",
        )

        response = self.client.delete(
            f"/api/v1/vehicles/{vehicle.id}/"
        )

        assert response.status_code == 404

        assert CustomerVehicle.objects.filter(
            id=vehicle.id
        ).exists()

    def test_set_default_vehicle(self):
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
        )

        second = CustomerVehicle.objects.create(
            customer=self.user,
            vehicle_variant=second_variant,
            nickname="Second Car",
            is_default=False,
        )

        response = self.client.patch(
            f"/api/v1/vehicles/{second.id}/set-default/",
            {},
            format="json",
        )

        assert response.status_code == 200

        first.refresh_from_db()
        second.refresh_from_db()

        assert first.is_default is False
        assert second.is_default is True

    def test_unauthenticated_user_cannot_access_vehicles(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            "/api/v1/vehicles/"
        )

        assert response.status_code == 401