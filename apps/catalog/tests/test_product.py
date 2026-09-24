import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import Brand, Category, Product, ProductType


@pytest.mark.django_db
class TestProductModel:

    def test_create_product(self):
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

        assert product.id is not None
        assert product.category == category
        assert product.brand == brand
        assert product.name == "Bosch Oil Filter"
        assert product.slug == "bosch-oil-filter"
        assert product.product_type == ProductType.AFTERMARKET
        assert product.is_active is True

    def test_product_can_exist_without_brand(self):
        category = Category.objects.create(
            name="Spark Plugs",
            slug="spark-plugs",
        )

        product = Product.objects.create(
            category=category,
            name="Universal Spark Plug",
            slug="universal-spark-plug",
        )

        assert product.brand is None

    def test_product_requires_category(self):
        product = Product(
            name="Test Product",
            slug="test-product",
        )

        with pytest.raises(ValidationError):
            product.full_clean()

    def test_product_slug_is_unique(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        Product.objects.create(
            category=category,
            name="Oil Filter",
            slug="oil-filter",
        )

        duplicate = Product(
            category=category,
            name="Another Oil Filter",
            slug="oil-filter",
        )

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_product_type_default(self):
        category = Category.objects.create(
            name="Belts",
            slug="belts",
        )

        product = Product.objects.create(
            category=category,
            name="Timing Belt",
            slug="timing-belt",
        )

        assert product.product_type == ProductType.AFTERMARKET

    def test_product_str(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        product = Product.objects.create(
            category=category,
            name="Air Filter",
            slug="air-filter",
        )

        assert str(product) == "Air Filter"