import pytest
from rest_framework.test import APIClient

from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductPartNumber,
    PartNumberType,
)


@pytest.mark.django_db
class TestProductPartNumberAPI:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def category(self):
        return Category.objects.create(
            name="Filters",
            slug="filters",
        )

    @pytest.fixture
    def brand(self):
        return Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

    @pytest.fixture
    def product(self, category, brand):
        return Product.objects.create(
            category=category,
            brand=brand,
            name="Oil Filter",
            slug="oil-filter",
        )

    @pytest.fixture
    def part_number(self, product, brand):
        return ProductPartNumber.objects.create(
            product=product,
            brand=brand,
            part_number="06J-115-403-Q",
            number_type=PartNumberType.OEM,
        )

    def test_list_part_numbers(
        self,
        client,
        part_number,
    ):
        response = client.get(
            "/api/v1/catalog/part-numbers/"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == str(part_number.id)

    def test_list_part_numbers_excludes_inactive(
        self,
        client,
        part_number,
    ):
        part_number.is_active = False
        part_number.save(update_fields=["is_active"])

        response = client.get(
            "/api/v1/catalog/part-numbers/"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 0
        assert data["results"] == []

    def test_retrieve_part_number(
        self,
        client,
        part_number,
    ):
        response = client.get(
            f"/api/v1/catalog/part-numbers/{part_number.id}/"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(part_number.id)
        assert data["part_number"] == "06J-115-403-Q"
        assert data["normalized_part_number"] == "06J115403Q"
        assert data["number_type"] == PartNumberType.OEM

    def test_retrieve_non_existing_part_number(
        self,
        client,
    ):
        response = client.get(
            "/api/v1/catalog/part-numbers/"
            "00000000-0000-0000-0000-000000000000/"
        )

        assert response.status_code == 404

    def test_create_part_number(
        self,
        client,
        product,
        brand,
    ):
        response = client.post(
            "/api/v1/catalog/part-numbers/",
            {
                "product": str(product.id),
                "brand": str(brand.id),
                "part_number": "ABC-123",
                "number_type": PartNumberType.OEM,
                "is_active": True,
            },
            format="json",
        )

        assert response.status_code == 201

        data = response.json()

        assert data["product"] == str(product.id)
        assert data["brand"] == str(brand.id)
        assert data["part_number"] == "ABC-123"
        assert data["normalized_part_number"] == "ABC123"
        assert data["number_type"] == PartNumberType.OEM

        assert ProductPartNumber.objects.filter(
            id=data["id"]
        ).exists()

    def test_create_part_number_without_brand(
        self,
        client,
        product,
    ):
        response = client.post(
            "/api/v1/catalog/part-numbers/",
            {
                "product": str(product.id),
                "part_number": "ABC-123",
                "number_type": PartNumberType.MANUFACTURER,
            },
            format="json",
        )

        assert response.status_code == 201

        data = response.json()

        assert data["brand"] is None
        assert data["normalized_part_number"] == "ABC123"

    def test_create_rejects_inactive_product(
        self,
        client,
        product,
    ):
        product.is_active = False
        product.save(update_fields=["is_active"])

        response = client.post(
            "/api/v1/catalog/part-numbers/",
            {
                "product": str(product.id),
                "part_number": "ABC123",
                "number_type": PartNumberType.OEM,
            },
            format="json",
        )

        assert response.status_code == 400
        assert "product" in response.json()

    def test_create_rejects_inactive_brand(
        self,
        client,
        product,
        brand,
    ):
        brand.is_active = False
        brand.save(update_fields=["is_active"])

        response = client.post(
            "/api/v1/catalog/part-numbers/",
            {
                "product": str(product.id),
                "brand": str(brand.id),
                "part_number": "ABC123",
                "number_type": PartNumberType.OEM,
            },
            format="json",
        )

        assert response.status_code == 400
        assert "brand" in response.json()

    def test_create_duplicate_part_number(
        self,
        client,
        part_number,
        product,
        brand,
    ):
        response = client.post(
            "/api/v1/catalog/part-numbers/",
            {
                "product": str(product.id),
                "brand": str(brand.id),
                "part_number": "06J115403Q",
                "number_type": PartNumberType.OEM,
            },
            format="json",
        )

        assert response.status_code == 400

    def test_update_part_number(
        self,
        client,
        part_number,
    ):
        response = client.patch(
            f"/api/v1/catalog/part-numbers/{part_number.id}/",
            {
                "part_number": "XYZ-789",
                "number_type": PartNumberType.MANUFACTURER,
            },
            format="json",
        )

        assert response.status_code == 200

        data = response.json()

        assert data["part_number"] == "XYZ-789"
        assert data["normalized_part_number"] == "XYZ789"
        assert data["number_type"] == PartNumberType.MANUFACTURER

    def test_update_normalized_part_number_is_read_only(
        self,
        client,
        part_number,
    ):
        response = client.patch(
            f"/api/v1/catalog/part-numbers/{part_number.id}/",
            {
                "normalized_part_number": "FAKEVALUE",
            },
            format="json",
        )

        assert response.status_code == 200

        data = response.json()

        assert data["normalized_part_number"] == "06J115403Q"

    def test_inactive_part_number_cannot_be_retrieved(
        self,
        client,
        part_number,
    ):
        part_number.is_active = False
        part_number.save(update_fields=["is_active"])

        response = client.get(
            f"/api/v1/catalog/part-numbers/{part_number.id}/"
        )

        assert response.status_code == 404