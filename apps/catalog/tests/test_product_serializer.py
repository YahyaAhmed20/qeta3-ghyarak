import pytest

from apps.catalog.api.serializers import ProductSerializer
from apps.catalog.models import Brand, Category, Product, ProductType


@pytest.mark.django_db
class TestProductSerializer:

    def test_serialize_product(self):
        category = Category.objects.create(
            name="Oil Filters",
            slug="oil-filters",
        )

        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        product = Product.objects.create(
            category=category,
            brand=brand,
            name="Bosch Oil Filter",
            slug="bosch-oil-filter",
            description="Engine oil filter",
            product_type=ProductType.AFTERMARKET,
            country_of_origin="Germany",
            warranty="12 months",
        )

        serializer = ProductSerializer(product)

        assert serializer.data["id"] == str(product.id)
        assert serializer.data["name"] == "Bosch Oil Filter"
        assert serializer.data["slug"] == "bosch-oil-filter"
        assert serializer.data["description"] == "Engine oil filter"
        assert serializer.data["product_type"] == ProductType.AFTERMARKET
        assert serializer.data["country_of_origin"] == "Germany"
        assert serializer.data["warranty"] == "12 months"
        assert serializer.data["is_active"] is True

    def test_serializer_includes_category_and_brand_ids(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        brand = Brand.objects.create(
            name="Mann",
            slug="mann",
        )

        product = Product.objects.create(
            category=category,
            brand=brand,
            name="Mann Filter",
            slug="mann-filter",
        )

        serializer = ProductSerializer(product)

        assert serializer.data["category"] == category.id
        assert serializer.data["brand"] == brand.id

    def test_serializer_allows_null_brand(self):
        category = Category.objects.create(
            name="Spark Plugs",
            slug="spark-plugs",
        )

        product = Product.objects.create(
            category=category,
            name="Universal Spark Plug",
            slug="universal-spark-plug",
        )

        serializer = ProductSerializer(product)

        assert serializer.data["brand"] is None