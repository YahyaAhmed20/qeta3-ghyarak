import pytest

from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductPartNumber,
    PartNumberType,
)
from apps.catalog.services.part_number import PartNumberService


@pytest.mark.django_db
class TestPartNumberService:

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
    def second_brand(self):
        return Brand.objects.create(
            name="Mann",
            slug="mann",
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
        result = PartNumberService.create_part_number(
            product=product,
            brand=brand,
            part_number="06J-115-403-Q",
            number_type=PartNumberType.OEM,
        )

        assert result.pk is not None
        assert result.product == product
        assert result.brand == brand
        assert result.part_number == "06J-115-403-Q"
        assert result.normalized_part_number == "06J115403Q"
        assert result.number_type == PartNumberType.OEM
        assert result.is_active is True

    def test_create_part_number_without_brand(self, product):
        result = PartNumberService.create_part_number(
            product=product,
            part_number="ABC-123",
            number_type=PartNumberType.MANUFACTURER,
        )

        assert result.brand is None
        assert result.normalized_part_number == "ABC123"

    def test_create_rejects_inactive_product(
        self,
        product,
    ):
        product.is_active = False
        product.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Product is not active"):
            PartNumberService.create_part_number(
                product=product,
                part_number="ABC123",
                number_type=PartNumberType.OEM,
            )

    def test_create_rejects_inactive_brand(
        self,
        product,
        brand,
    ):
        brand.is_active = False
        brand.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Brand is not active"):
            PartNumberService.create_part_number(
                product=product,
                brand=brand,
                part_number="ABC123",
                number_type=PartNumberType.OEM,
            )

    def test_update_part_number(
        self,
        product,
        brand,
        second_brand,
    ):
        part = PartNumberService.create_part_number(
            product=product,
            brand=brand,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
        )

        updated = PartNumberService.update_part_number(
            part_number_id=part.id,
            brand=second_brand,
            part_number="XYZ-789",
            number_type=PartNumberType.MANUFACTURER,
        )

        assert updated.brand == second_brand
        assert updated.part_number == "XYZ-789"
        assert updated.normalized_part_number == "XYZ789"
        assert updated.number_type == PartNumberType.MANUFACTURER

    def test_update_can_change_product(
        self,
        product,
        category,
    ):
        second_product = Product.objects.create(
            category=category,
            name="Air Filter",
            slug="air-filter",
        )

        part = PartNumberService.create_part_number(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
        )

        updated = PartNumberService.update_part_number(
            part_number_id=part.id,
            product=second_product,
        )

        assert updated.product == second_product

    def test_update_rejects_inactive_product(
        self,
        product,
    ):
        part = PartNumberService.create_part_number(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
        )

        product.is_active = False
        product.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Product is not active"):
            PartNumberService.update_part_number(
                part_number_id=part.id,
                product=product,
            )

    def test_update_rejects_inactive_brand(
        self,
        product,
        brand,
    ):
        part = PartNumberService.create_part_number(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
        )

        brand.is_active = False
        brand.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Brand is not active"):
            PartNumberService.update_part_number(
                part_number_id=part.id,
                brand=brand,
            )

    def test_update_part_number_not_found(
        self,
        product,
    ):
        with pytest.raises(ValueError, match="Part number not found"):
            PartNumberService.update_part_number(
                part_number_id="00000000-0000-0000-0000-000000000000",
                product=product,
            )

    def test_deactivate_part_number(
        self,
        product,
    ):
        part = PartNumberService.create_part_number(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
        )

        result = PartNumberService.deactivate_part_number(
            part_number_id=part.id,
        )

        assert result.is_active is False

        part.refresh_from_db()

        assert part.is_active is False

    def test_deactivate_part_number_not_found(self):
        with pytest.raises(ValueError, match="Part number not found"):
            PartNumberService.deactivate_part_number(
                part_number_id="00000000-0000-0000-0000-000000000000",
            )

    def test_activate_part_number(
        self,
        product,
    ):
        part = PartNumberService.create_part_number(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
            is_active=False,
        )

        result = PartNumberService.activate_part_number(
            part_number_id=part.id,
        )

        assert result.is_active is True

        part.refresh_from_db()

        assert part.is_active is True

    def test_activate_rejects_inactive_product(
        self,
        product,
    ):
        part = PartNumberService.create_part_number(
            product=product,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
            is_active=False,
        )

        product.is_active = False
        product.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Product is not active"):
            PartNumberService.activate_part_number(
                part_number_id=part.id,
            )

    def test_activate_rejects_inactive_brand(
        self,
        product,
        brand,
    ):
        part = PartNumberService.create_part_number(
            product=product,
            brand=brand,
            part_number="ABC123",
            number_type=PartNumberType.OEM,
            is_active=False,
        )

        brand.is_active = False
        brand.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Brand is not active"):
            PartNumberService.activate_part_number(
                part_number_id=part.id,
            )

    def test_activate_part_number_not_found(self):
        with pytest.raises(ValueError, match="Part number not found"):
            PartNumberService.activate_part_number(
                part_number_id="00000000-0000-0000-0000-000000000000",
            )

    def test_create_duplicate_part_number_is_rejected(
        self,
        product,
    ):
        PartNumberService.create_part_number(
            product=product,
            part_number="ABC-123",
            number_type=PartNumberType.OEM,
        )

        with pytest.raises(Exception):
            PartNumberService.create_part_number(
                product=product,
                part_number="ABC123",
                number_type=PartNumberType.OEM,
            )