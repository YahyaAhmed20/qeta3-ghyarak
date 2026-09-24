import pytest

from apps.catalog.models import (
    Brand,
    Category,
    CompatibilityStatus,
    Product,
    ProductCompatibility,
    ProductType,
)
from apps.catalog.selectors.compatibility import CompatibilitySelector
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
def second_product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Air Filter",
        slug="air-filter",
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
        slug="octavia-a5-1-6-mpi",
    )


@pytest.fixture
def second_vehicle_variant(vehicle_variant):
    return VehicleVariant.objects.create(
        engine=vehicle_variant.engine,
        name="Octavia A5 1.6 MPI DSG",
        slug="octavia-a5-1-6-mpi-dsg",
    )


@pytest.mark.django_db
class TestCompatibilitySelector:

    def test_get_approved_for_product_returns_only_approved(
        self,
        product,
        vehicle_variant,
        second_vehicle_variant,
    ):
        approved = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=second_vehicle_variant,
            status=CompatibilityStatus.PENDING,
        )

        results = CompatibilitySelector.get_approved_for_product(
            product_id=product.id,
        )

        assert list(results) == [approved]

    def test_get_approved_for_product_excludes_inactive_product(
        self,
        product,
        vehicle_variant,
    ):
        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        product.is_active = False
        product.save(update_fields=["is_active"])

        results = CompatibilitySelector.get_approved_for_product(
            product_id=product.id,
        )

        assert list(results) == []

    def test_get_approved_for_product_excludes_inactive_vehicle(
        self,
        product,
        vehicle_variant,
    ):
        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        vehicle_variant.is_active = False
        vehicle_variant.save(update_fields=["is_active"])

        results = CompatibilitySelector.get_approved_for_product(
            product_id=product.id,
        )

        assert list(results) == []

    def test_get_approved_for_vehicle_returns_only_approved_products(
        self,
        product,
        second_product,
        vehicle_variant,
    ):
        approved = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        ProductCompatibility.objects.create(
            product=second_product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.PENDING,
        )

        results = CompatibilitySelector.get_approved_for_vehicle(
            vehicle_variant_id=vehicle_variant.id,
        )

        assert list(results) == [approved]

    def test_get_approved_for_vehicle_excludes_inactive_product(
        self,
        product,
        vehicle_variant,
    ):
        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        product.is_active = False
        product.save(update_fields=["is_active"])

        results = CompatibilitySelector.get_approved_for_vehicle(
            vehicle_variant_id=vehicle_variant.id,
        )

        assert list(results) == []

    def test_get_approved_for_vehicle_excludes_inactive_vehicle(
        self,
        product,
        vehicle_variant,
    ):
        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        vehicle_variant.is_active = False
        vehicle_variant.save(update_fields=["is_active"])

        results = CompatibilitySelector.get_approved_for_vehicle(
            vehicle_variant_id=vehicle_variant.id,
        )

        assert list(results) == []

    def test_get_approved_compatibility_returns_approved(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        result = CompatibilitySelector.get_approved_compatibility(
            compatibility_id=compatibility.id,
        )

        assert result == compatibility

    def test_get_approved_compatibility_returns_none_for_pending(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.PENDING,
        )

        result = CompatibilitySelector.get_approved_compatibility(
            compatibility_id=compatibility.id,
        )

        assert result is None

    def test_get_approved_compatibility_returns_none_for_inactive_product(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        product.is_active = False
        product.save(update_fields=["is_active"])

        result = CompatibilitySelector.get_approved_compatibility(
            compatibility_id=compatibility.id,
        )

        assert result is None

    def test_get_approved_compatibility_returns_none_for_inactive_vehicle(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
        )

        vehicle_variant.is_active = False
        vehicle_variant.save(update_fields=["is_active"])

        result = CompatibilitySelector.get_approved_compatibility(
            compatibility_id=compatibility.id,
        )

        assert result is None