import pytest
from rest_framework.test import APIClient

from apps.catalog.models import Brand, Category, Product


@pytest.mark.django_db
class TestProductAPI:

    def setup_method(self):
        self.client = APIClient()

        self.category = Category.objects.create(
            name="Oil Filters",
            slug="oil-filters",
        )

        self.brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        self.product = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name="Bosch Oil Filter",
            slug="bosch-oil-filter",
        )

    def test_list_products(self):
        response = self.client.get("/api/v1/catalog/products/")

        assert response.status_code == 200
        assert response.data["count"] == 1

        product = response.data["results"][0]

        assert product["id"] == str(self.product.id)
        assert product["name"] == "Bosch Oil Filter"

    def test_retrieve_product(self):
        response = self.client.get(
            f"/api/v1/catalog/products/{self.product.id}/"
        )

        assert response.status_code == 200
        assert response.data["id"] == str(self.product.id)
        assert response.data["name"] == "Bosch Oil Filter"

    def test_list_products_excludes_inactive_products(self):
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])

        response = self.client.get("/api/v1/catalog/products/")

        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_retrieve_non_existing_product(self):
        response = self.client.get(
            "/api/v1/catalog/products/"
            "00000000-0000-0000-0000-000000000000/"
        )

        assert response.status_code == 404