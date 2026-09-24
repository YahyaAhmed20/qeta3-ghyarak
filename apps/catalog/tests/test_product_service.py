import pytest

from apps.catalog.models import Brand, Category, Product, ProductType
from apps.catalog.services.product import ProductService


@pytest.mark.django_db
class TestProductService:

    def test_create_product(self):
        category = Category.objects.create(
            name="Oil Filters",
            slug="oil-filters",
        )

        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        product = ProductService.create_product(
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
        assert product.is_active is True

    def test_create_product_without_brand(self):
        category = Category.objects.create(
            name="Spark Plugs",
            slug="spark-plugs",
        )

        product = ProductService.create_product(
            category=category,
            name="Universal Spark Plug",
            slug="universal-spark-plug",
        )

        assert product.brand is None

    def test_create_product_rejects_inactive_category(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
            is_active=False,
        )

        with pytest.raises(ValueError, match="Category is not active."):
            ProductService.create_product(
                category=category,
                name="Oil Filter",
                slug="oil-filter",
            )

    def test_create_product_rejects_inactive_brand(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
            is_active=False,
        )

        with pytest.raises(ValueError, match="Brand is not active."):
            ProductService.create_product(
                category=category,
                brand=brand,
                name="Bosch Filter",
                slug="bosch-filter",
            )

    def test_update_product(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        product = Product.objects.create(
            category=category,
            name="Old Filter",
            slug="old-filter",
        )

        updated = ProductService.update_product(
            product_id=product.id,
            name="New Filter",
            slug="new-filter",
            description="Updated description",
        )

        assert updated.name == "New Filter"
        assert updated.slug == "new-filter"
        assert updated.description == "Updated description"

    def test_update_product_can_change_category_and_brand(self):
        category_one = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        category_two = Category.objects.create(
            name="Spark Plugs",
            slug="spark-plugs",
        )

        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        product = Product.objects.create(
            category=category_one,
            name="Product",
            slug="product",
        )

        updated = ProductService.update_product(
            product_id=product.id,
            category=category_two,
            brand=brand,
        )

        assert updated.category == category_two
        assert updated.brand == brand

    def test_update_product_rejects_inactive_category(self):
        active_category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        inactive_category = Category.objects.create(
            name="Belts",
            slug="belts",
            is_active=False,
        )

        product = Product.objects.create(
            category=active_category,
            name="Product",
            slug="product",
        )

        with pytest.raises(ValueError, match="Category is not active."):
            ProductService.update_product(
                product_id=product.id,
                category=inactive_category,
            )

    def test_update_product_rejects_inactive_brand(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        active_brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        inactive_brand = Brand.objects.create(
            name="Mann",
            slug="mann",
            is_active=False,
        )

        product = Product.objects.create(
            category=category,
            brand=active_brand,
            name="Product",
            slug="product",
        )

        with pytest.raises(ValueError, match="Brand is not active."):
            ProductService.update_product(
                product_id=product.id,
                brand=inactive_brand,
            )

    def test_deactivate_product(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        product = Product.objects.create(
            category=category,
            name="Oil Filter",
            slug="oil-filter",
        )

        updated = ProductService.deactivate_product(
            product_id=product.id,
        )

        assert updated.is_active is False

    def test_activate_product(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        product = Product.objects.create(
            category=category,
            name="Oil Filter",
            slug="oil-filter",
            is_active=False,
        )

        updated = ProductService.activate_product(
            product_id=product.id,
        )

        assert updated.is_active is True

    def test_update_product_not_found(self):
        with pytest.raises(ValueError, match="Product not found."):
            ProductService.update_product(
                product_id="00000000-0000-0000-0000-000000000000",
                name="Test",
            )

    def test_deactivate_product_not_found(self):
        with pytest.raises(ValueError, match="Product not found."):
            ProductService.deactivate_product(
                product_id="00000000-0000-0000-0000-000000000000",
            )