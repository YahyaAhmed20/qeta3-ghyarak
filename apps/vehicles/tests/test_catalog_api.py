import pytest
from rest_framework.test import APIClient

from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)


@pytest.mark.django_db
class TestVehicleCatalogAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_list_makes(self, vehicle_variant):
        make = vehicle_variant.engine.generation.model.make

        response = self.client.get(
            "/api/v1/vehicles/catalog/makes/",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(make.id)
        assert response.data[0]["name"] == "Skoda"
        assert response.data[0]["slug"] == "skoda"

    def test_list_models_for_make(self, vehicle_variant):
        model = vehicle_variant.engine.generation.model
        make = model.make

        response = self.client.get(
            f"/api/v1/vehicles/catalog/makes/{make.id}/models/",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(model.id)
        assert response.data[0]["name"] == "Octavia"

    def test_list_generations_for_model(self, vehicle_variant):
        generation = vehicle_variant.engine.generation
        model = generation.model

        response = self.client.get(
            f"/api/v1/vehicles/catalog/models/{model.id}/generations/",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(generation.id)
        assert response.data[0]["name"] == "A7"
        assert response.data[0]["year_from"] == 2013
        assert response.data[0]["year_to"] == 2019

    def test_list_engines_for_generation(self, vehicle_variant):
        engine = vehicle_variant.engine
        generation = engine.generation

        response = self.client.get(
            f"/api/v1/vehicles/catalog/generations/{generation.id}/engines/",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(engine.id)
        assert response.data[0]["name"] == "1.6 MPI"
        assert response.data[0]["code"] == "CWVA"
        assert response.data[0]["displacement_cc"] == 1598
        assert response.data[0]["fuel_type"] == "Petrol"
        assert response.data[0]["power_hp"] == 110

    def test_list_variants_for_engine(self, vehicle_variant):
        engine = vehicle_variant.engine

        response = self.client.get(
            f"/api/v1/vehicles/catalog/engines/{engine.id}/variants/",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(vehicle_variant.id)
        assert response.data[0]["name"] == "1.6 MPI Automatic"
        assert response.data[0]["slug"] == "1-6-mpi-automatic"
        assert response.data[0]["transmission"] == "Automatic"
        assert response.data[0]["market"] == "EU"

    def test_catalog_is_public(self, vehicle_variant):
        make = vehicle_variant.engine.generation.model.make

        response = self.client.get(
            f"/api/v1/vehicles/catalog/makes/{make.id}/models/",
        )

        assert response.status_code == 200

    def test_inactive_make_is_not_returned(self, vehicle_variant):
        inactive_make = VehicleMake.objects.create(
            name="BMW",
            slug="bmw",
            is_active=False,
        )

        response = self.client.get(
            "/api/v1/vehicles/catalog/makes/",
        )

        assert response.status_code == 200
        assert all(
            item["id"] != str(inactive_make.id)
            for item in response.data
        )

    def test_inactive_model_is_not_returned(self, vehicle_variant):
        make = vehicle_variant.engine.generation.model.make

        inactive_model = VehicleModel.objects.create(
            make=make,
            name="Inactive Model",
            slug="inactive-model",
            is_active=False,
        )

        response = self.client.get(
            f"/api/v1/vehicles/catalog/makes/{make.id}/models/",
        )

        assert response.status_code == 200
        assert all(
            item["id"] != str(inactive_model.id)
            for item in response.data
        )

    def test_inactive_generation_is_not_returned(self, vehicle_variant):
        model = vehicle_variant.engine.generation.model

        inactive_generation = VehicleGeneration.objects.create(
            model=model,
            name="Inactive Generation",
            slug="inactive-generation",
            is_active=False,
        )

        response = self.client.get(
            f"/api/v1/vehicles/catalog/models/{model.id}/generations/",
        )

        assert response.status_code == 200
        assert all(
            item["id"] != str(inactive_generation.id)
            for item in response.data
        )

    def test_inactive_engine_is_not_returned(self, vehicle_variant):
        generation = vehicle_variant.engine.generation

        inactive_engine = VehicleEngine.objects.create(
            generation=generation,
            name="Inactive Engine",
            code="INACTIVE",
            is_active=False,
        )

        response = self.client.get(
            f"/api/v1/vehicles/catalog/generations/{generation.id}/engines/",
        )

        assert response.status_code == 200
        assert all(
            item["id"] != str(inactive_engine.id)
            for item in response.data
        )

    def test_inactive_variant_is_not_returned(self, vehicle_variant):
        engine = vehicle_variant.engine

        inactive_variant = VehicleVariant.objects.create(
            engine=engine,
            name="Inactive Variant",
            slug="inactive-variant",
            is_active=False,
        )

        response = self.client.get(
            f"/api/v1/vehicles/catalog/engines/{engine.id}/variants/",
        )

        assert response.status_code == 200
        assert all(
            item["id"] != str(inactive_variant.id)
            for item in response.data
        )

    def test_unknown_make_returns_404(self):
        response = self.client.get(
            "/api/v1/vehicles/catalog/makes/"
            "00000000-0000-0000-0000-000000000000/models/",
        )

        assert response.status_code == 404

    def test_unknown_model_returns_404(self):
        response = self.client.get(
            "/api/v1/vehicles/catalog/models/"
            "00000000-0000-0000-0000-000000000000/generations/",
        )

        assert response.status_code == 404

    def test_unknown_generation_returns_404(self):
        response = self.client.get(
            "/api/v1/vehicles/catalog/generations/"
            "00000000-0000-0000-0000-000000000000/engines/",
        )

        assert response.status_code == 404

    def test_unknown_engine_returns_404(self):
        response = self.client.get(
            "/api/v1/vehicles/catalog/engines/"
            "00000000-0000-0000-0000-000000000000/variants/",
        )

        assert response.status_code == 404

    def test_wrong_hierarchy_returns_empty_list(
        self,
        vehicle_variant,
    ):
        make = vehicle_variant.engine.generation.model.make

        other_make = VehicleMake.objects.create(
            name="BMW",
            slug="bmw",
        )

        response = self.client.get(
            f"/api/v1/vehicles/catalog/makes/{other_make.id}/models/",
        )

        assert response.status_code == 200
        assert response.data == []