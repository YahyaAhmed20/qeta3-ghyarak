import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductPartNumber,
    PartNumberType,
)


@pytest.mark.django_db
class TestProductPartNumberModel:

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

    def test_create_part_number(self, product, brand):
        part_number = ProductPartNumber.objects.create(
            product=product,
            brand=brand,
            part_number="06J 115 403 Q",
            number_type=PartNumberType.OEM,
        )

        assert part_number.product == product
        assert part_number.brand == brand
        assert part_number.part_number == "06J 115 403 Q"
        assert part_number.number_type == PartNumberType.OEM
        assert part_number.is_active is True

    def test_normalizes_spaces_and_separators(self, product):
        part_number = ProductPartNumber.objects.create(
            product=product,
            part_number="06J-115/403.Q",
        )

        assert part_number.normalized_part_number == "06J115403Q"

    def test_normalizes_lowercase_to_uppercase(self, product):
        part_number = ProductPartNumber.objects.create(
            product=product,
            part_number="abc-123-def",
        )

        assert part_number.normalized_part_number == "ABC123DEF"

    def test_rejects_empty_part_number(self, product):
        part_number = ProductPartNumber(
            product=product,
            part_number="   ",
        )

        with pytest.raises(ValidationError):
            part_number.full_clean()

    def test_brand_is_optional(self, product):
        part_number = ProductPartNumber.objects.create(
            product=product,
            part_number="ABC123",
        )

        assert part_number.brand is None

    def test_allows_multiple_part_numbers_for_same_product(self, product):
        first = ProductPartNumber.objects.create(
            product=product,
            part_number="ABC123",
        )

        second = ProductPartNumber.objects.create(
            product=product,
            part_number="XYZ789",
        )

        assert first.product == second.product
        assert first.id != second.id
        assert ProductPartNumber.objects.filter(product=product).count() == 2

    def test_prevents_duplicate_part_number_for_same_product(
        self,
        product,
    ):
        ProductPartNumber.objects.create(
            product=product,
            part_number="ABC-123",
            number_type=PartNumberType.OEM,
        )

        duplicate = ProductPartNumber(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
        )

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_same_part_number_can_exist_for_different_products(
        self,
        category,
    ):
        product_one = Product.objects.create(
            category=category,
            name="Oil Filter One",
            slug="oil-filter-one",
        )

        product_two = Product.objects.create(
            category=category,
            name="Oil Filter Two",
            slug="oil-filter-two",
        )

        ProductPartNumber.objects.create(
            product=product_one,
            part_number="ABC123",
        )

        ProductPartNumber.objects.create(
            product=product_two,
            part_number="ABC123",
        )

        assert (
            ProductPartNumber.objects.filter(
                normalized_part_number="ABC123"
            ).count()
            == 2
        )

    def test_same_normalized_number_can_exist_with_different_types(
        self,
        product,
    ):
        ProductPartNumber.objects.create(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
        )

        second = ProductPartNumber.objects.create(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.CROSS_REFERENCE,
        )

        assert second.number_type == PartNumberType.CROSS_REFERENCE

    def test_inactive_part_number(self, product):
        part_number = ProductPartNumber.objects.create(
            product=product,
            part_number="ABC123",
            is_active=False,
        )

        assert part_number.is_active is False

    def test_str_returns_original_part_number(self, product):
        part_number = ProductPartNumber.objects.create(
            product=product,
            part_number="06J 115 403 Q",
        )

        assert str(part_number) == "06J 115 403 Q"