import pytest

from apps.catalog.api.part_number_serializers import ProductPartNumberSerializer
from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductPartNumber,
    PartNumberType,
)


@pytest.mark.django_db
class TestProductPartNumberSerializer:

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

    def test_serialize_part_number(self, product, brand):
        part_number = ProductPartNumber.objects.create(
            product=product,
            brand=brand,
            part_number="06J-115-403-Q",
            number_type=PartNumberType.OEM,
        )

        serializer = ProductPartNumberSerializer(part_number)

        data = serializer.data

        assert data["id"] == str(part_number.id)
        assert data["product"] == product.id
        assert data["brand"] == brand.id
        assert data["part_number"] == "06J-115-403-Q"
        assert data["normalized_part_number"] == "06J115403Q"
        assert data["number_type"] == PartNumberType.OEM
        assert data["is_active"] is True

    def test_serializer_allows_null_brand(self, product):
        serializer = ProductPartNumberSerializer(
            data={
                "product": str(product.id),
                "brand": None,
                "part_number": "ABC-123",
                "number_type": PartNumberType.MANUFACTURER,
                "is_active": True,
            }
        )

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()

        assert instance.brand is None
        assert instance.normalized_part_number == "ABC123"

    def test_serializer_rejects_inactive_product(
        self,
        product,
    ):
        product.is_active = False
        product.save(update_fields=["is_active"])

        serializer = ProductPartNumberSerializer(
            data={
                "product": str(product.id),
                "part_number": "ABC123",
                "number_type": PartNumberType.OEM,
            }
        )

        assert not serializer.is_valid()
        assert "product" in serializer.errors

    def test_serializer_rejects_inactive_brand(
        self,
        product,
        brand,
    ):
        brand.is_active = False
        brand.save(update_fields=["is_active"])

        serializer = ProductPartNumberSerializer(
            data={
                "product": str(product.id),
                "brand": str(brand.id),
                "part_number": "ABC123",
                "number_type": PartNumberType.OEM,
            }
        )

        assert not serializer.is_valid()
        assert "brand" in serializer.errors

    def test_normalized_part_number_is_read_only(
        self,
        product,
    ):
        serializer = ProductPartNumberSerializer(
            data={
                "product": str(product.id),
                "part_number": "ABC-123",
                "normalized_part_number": "FAKEVALUE",
                "number_type": PartNumberType.OEM,
            }
        )

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()

        assert instance.normalized_part_number == "ABC123"