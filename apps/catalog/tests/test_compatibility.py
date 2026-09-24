import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductCompatibility,
    ProductType,
    CompatibilityStatus,
)
from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Engine Parts",
        slug="engine-parts",
    )


@pytest.fixture
def brand(db):
    return Brand.objects.create(
        name="Bosch",
        slug="bosch",
    )


@pytest.fixture
def product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Oil Filter",
        slug="oil-filter",
        product_type=ProductType.AFTERMARKET,
    )


@pytest.fixture
def vehicle_variant(db):
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
        code="BSE",
    )

    return VehicleVariant.objects.create(
        engine=engine,
        name="Octavia A5 1.6 MPI",
    )


@pytest.mark.django_db
class TestProductCompatibilityModel:

    def test_creates_product_compatibility(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        assert compatibility.product == product
        assert compatibility.vehicle_variant == vehicle_variant
        assert compatibility.status == CompatibilityStatus.PENDING
        assert compatibility.notes == ""

    def test_default_status_is_pending(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        assert compatibility.status == CompatibilityStatus.PENDING

    def test_notes_are_optional(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            notes="Compatible with standard oil filter housing.",
        )

        assert compatibility.notes == (
            "Compatible with standard oil filter housing."
        )

    def test_same_product_and_vehicle_cannot_be_duplicated(
        self,
        product,
        vehicle_variant,
    ):
        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        with pytest.raises(IntegrityError):
            ProductCompatibility.objects.create(
                product=product,
                vehicle_variant=vehicle_variant,
            )

    def test_inactive_product_is_rejected(
        self,
        product,
        vehicle_variant,
    ):
        product.is_active = False
        product.save(update_fields=["is_active"])

        compatibility = ProductCompatibility(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        with pytest.raises(ValidationError) as exc_info:
            compatibility.full_clean()

        assert "product" in exc_info.value.message_dict

    def test_same_product_can_have_multiple_vehicle_variants(
        self,
        product,
        vehicle_variant,
        db,
    ):
        second_variant = VehicleVariant.objects.create(
            engine=vehicle_variant.engine,
            name="Octavia A5 1.6 MPI DSG",
            slug="octavia-a5-1-6-mpi-dsg",
        )

        first = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        second = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=second_variant,
        )

        assert first.product == product
        assert second.product == product
        assert first.vehicle_variant != second.vehicle_variant

    def test_same_vehicle_can_have_multiple_products(
        self,
        product,
        vehicle_variant,
        category,
        brand,
    ):
        second_product = Product.objects.create(
            category=category,
            brand=brand,
            name="Air Filter",
            slug="air-filter",
            product_type=ProductType.AFTERMARKET,
        )

        first = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        second = ProductCompatibility.objects.create(
            product=second_product,
            vehicle_variant=vehicle_variant,
        )

        assert first.vehicle_variant == vehicle_variant
        assert second.vehicle_variant == vehicle_variant
        assert first.product != second.product

    def test_all_status_values_are_supported(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        for status in CompatibilityStatus.values:
            compatibility.status = status
            compatibility.full_clean()
            compatibility.save(update_fields=["status", "updated_at"])

            assert compatibility.status == status