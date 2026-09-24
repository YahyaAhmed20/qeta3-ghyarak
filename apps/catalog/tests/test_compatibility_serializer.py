import pytest

from apps.catalog.api.serializers import (
    ProductCompatibilitySerializer,
)
from apps.catalog.models import (
    Brand,
    Category,
    CompatibilityStatus,
    Product,
    ProductCompatibility,
    ProductType,
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
class TestProductCompatibilitySerializer:

    def test_valid_data(
        self,
        product,
        vehicle_variant,
    ):
        serializer = ProductCompatibilitySerializer(
            data={
                "product": str(product.id),
                "vehicle_variant": str(vehicle_variant.id),
                "notes": "Fits standard housing.",
            }
        )

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["product"] == product
        assert (
            serializer.validated_data["vehicle_variant"]
            == vehicle_variant
        )
        assert (
            serializer.validated_data["notes"]
            == "Fits standard housing."
        )

    def test_status_is_read_only(
        self,
        product,
        vehicle_variant,
    ):
        serializer = ProductCompatibilitySerializer(
            data={
                "product": str(product.id),
                "vehicle_variant": str(vehicle_variant.id),
                "status": CompatibilityStatus.APPROVED,
            }
        )

        assert serializer.is_valid(), serializer.errors
        assert "status" not in serializer.validated_data

    def test_inactive_product_is_rejected(
        self,
        product,
        vehicle_variant,
    ):
        product.is_active = False
        product.save(update_fields=["is_active"])

        serializer = ProductCompatibilitySerializer(
            data={
                "product": str(product.id),
                "vehicle_variant": str(vehicle_variant.id),
            }
        )

        assert not serializer.is_valid()
        assert "product" in serializer.errors

    def test_inactive_vehicle_variant_is_rejected(
        self,
        product,
        vehicle_variant,
    ):
        vehicle_variant.is_active = False
        vehicle_variant.save(update_fields=["is_active"])

        serializer = ProductCompatibilitySerializer(
            data={
                "product": str(product.id),
                "vehicle_variant": str(vehicle_variant.id),
            }
        )

        assert not serializer.is_valid()
        assert "vehicle_variant" in serializer.errors

    def test_duplicate_product_vehicle_is_rejected(
        self,
        product,
        vehicle_variant,
    ):
        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        serializer = ProductCompatibilitySerializer(
            data={
                "product": str(product.id),
                "vehicle_variant": str(vehicle_variant.id),
            }
        )

        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_same_product_with_different_vehicle_is_valid(
        self,
        product,
        vehicle_variant,
        second_vehicle_variant,
    ):
        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        serializer = ProductCompatibilitySerializer(
            data={
                "product": str(product.id),
                "vehicle_variant": str(second_vehicle_variant.id),
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_same_vehicle_with_different_product_is_valid(
        self,
        product,
        second_product,
        vehicle_variant,
    ):
        ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        serializer = ProductCompatibilitySerializer(
            data={
                "product": str(second_product.id),
                "vehicle_variant": str(vehicle_variant.id),
            }
        )

        assert serializer.is_valid(), serializer.errors

    def test_serializer_output(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = ProductCompatibility.objects.create(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.APPROVED,
            notes="Verified fitment.",
        )

        serializer = ProductCompatibilitySerializer(
            compatibility
        )

        data = serializer.data

        assert data["id"] == str(compatibility.id)
        assert data["product"] == product.id
        assert data["vehicle_variant"] == vehicle_variant.id
        assert data["status"] == CompatibilityStatus.APPROVED
        assert data["notes"] == "Verified fitment."
        assert "created_at" in data
        assert "updated_at" in data