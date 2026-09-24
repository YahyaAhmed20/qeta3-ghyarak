import pytest
from rest_framework.test import APIClient

from apps.catalog.models import (
    Brand,
    Category,
    CompatibilityStatus,
    Product,
    ProductCompatibility,
)
from apps.catalog.services.compatibility import CompatibilityService
from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)


@pytest.mark.django_db
class TestProductCompatibilityAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def product(self):
        category = Category.objects.create(
            name="Oil Filters",
            slug="oil-filters",
        )

        brand = Brand.objects.create(
            name="MANN",
            slug="mann",
        )

        return Product.objects.create(
            category=category,
            brand=brand,
            name="MANN Oil Filter",
            slug="mann-oil-filter",
        )

    @pytest.fixture
    def vehicle_variant(self):
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
        )

        engine = VehicleEngine.objects.create(
            generation=generation,
            name="1.6 MPI",
        )

        return VehicleVariant.objects.create(
            engine=engine,
            name="Octavia A5 1.6 MPI",
            slug="octavia-a5-1-6-mpi",
        )

    @pytest.fixture
    def approved_compatibility(self, product, vehicle_variant):
        compatibility = CompatibilityService.create_compatibility(
            product=product,
            vehicle_variant=vehicle_variant,
            notes="Verified fitment.",
        )

        return CompatibilityService.approve_compatibility(
            compatibility_id=compatibility.id,
        )

    def test_product_compatibility_list_returns_approved_only(
        self,
        api_client,
        product,
        vehicle_variant,
    ):
        compatibility = CompatibilityService.create_compatibility(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        url = (
            f"/api/v1/catalog/products/"
            f"{product.id}/compatibilities/"
        )

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["count"] == 0

        compatibility.status = CompatibilityStatus.APPROVED
        compatibility.save(update_fields=["status"])

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 1

        item = response.data["results"][0]

        assert item["id"] == str(compatibility.id)
        assert item["product"] == product.id
        assert item["vehicle_variant"] == vehicle_variant.id
        assert item["status"] == CompatibilityStatus.APPROVED

    def test_product_compatibility_list_does_not_return_rejected(
        self,
        api_client,
        product,
        vehicle_variant,
    ):
        compatibility = CompatibilityService.create_compatibility(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        CompatibilityService.reject_compatibility(
            compatibility_id=compatibility.id,
            notes="Not confirmed.",
        )

        url = (
            f"/api/v1/catalog/products/"
            f"{product.id}/compatibilities/"
        )

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_product_compatibility_detail_returns_approved(
        self,
        api_client,
        approved_compatibility,
    ):
        url = (
            f"/api/v1/catalog/compatibilities/"
            f"{approved_compatibility.id}/"
        )

        response = api_client.get(url)

        assert response.status_code == 200

        assert response.data["id"] == str(
            approved_compatibility.id
        )
        assert response.data["product"] == (
            approved_compatibility.product.id
        )
        assert response.data["vehicle_variant"] == (
            approved_compatibility.vehicle_variant.id
        )
        assert response.data["status"] == CompatibilityStatus.APPROVED
        assert response.data["notes"] == "Verified fitment."

    def test_product_compatibility_detail_hides_pending(
        self,
        api_client,
        product,
        vehicle_variant,
    ):
        compatibility = CompatibilityService.create_compatibility(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        url = (
            f"/api/v1/catalog/compatibilities/"
            f"{compatibility.id}/"
        )

        response = api_client.get(url)

        assert response.status_code == 404

    def test_product_compatibility_detail_hides_rejected(
        self,
        api_client,
        product,
        vehicle_variant,
    ):
        compatibility = CompatibilityService.create_compatibility(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        CompatibilityService.reject_compatibility(
            compatibility_id=compatibility.id,
            notes="Rejected.",
        )

        url = (
            f"/api/v1/catalog/compatibilities/"
            f"{compatibility.id}/"
        )

        response = api_client.get(url)

        assert response.status_code == 404

    def test_product_compatibility_list_requires_active_product(
        self,
        api_client,
        product,
        vehicle_variant,
    ):
        compatibility = CompatibilityService.create_compatibility(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        compatibility.status = CompatibilityStatus.APPROVED
        compatibility.save(update_fields=["status"])

        product.is_active = False
        product.save(update_fields=["is_active"])

        url = (
            f"/api/v1/catalog/products/"
            f"{product.id}/compatibilities/"
        )

        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 0