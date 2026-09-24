import pytest

from apps.catalog.models import (
    Brand,
    Category,
    CompatibilityStatus,
    Product,
    ProductCompatibility,
    ProductType,
)
from apps.catalog.services.compatibility import CompatibilityService
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
def product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Oil Filter",
        slug="oil-filter",
        product_type=ProductType.AFTERMARKET,
    )


@pytest.mark.django_db
class TestCompatibilityService:

    def test_create_compatibility(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = (
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )
        )

        assert compatibility.product == product
        assert compatibility.vehicle_variant == vehicle_variant
        assert compatibility.status == CompatibilityStatus.PENDING
        assert compatibility.notes == ""

    def test_create_compatibility_with_notes(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = (
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
                notes="Fits standard oil filter housing.",
            )
        )

        assert compatibility.notes == (
            "Fits standard oil filter housing."
        )

    def test_create_rejects_inactive_product(
        self,
        product,
        vehicle_variant,
    ):
        product.is_active = False
        product.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Product is not active"):
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )

    def test_create_rejects_inactive_vehicle_variant(
        self,
        product,
        vehicle_variant,
    ):
        vehicle_variant.is_active = False
        vehicle_variant.save(update_fields=["is_active"])

        with pytest.raises(
            ValueError,
            match="Vehicle variant is not active",
        ):
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )

    def test_approve_pending_compatibility(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = (
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )
        )

        approved = (
            CompatibilityService.approve_compatibility(
                compatibility_id=compatibility.id,
            )
        )

        assert approved.status == CompatibilityStatus.APPROVED

    def test_cannot_approve_already_approved(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = (
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )
        )

        CompatibilityService.approve_compatibility(
            compatibility_id=compatibility.id,
        )

        with pytest.raises(
            ValueError,
            match="Only pending compatibility can be approved",
        ):
            CompatibilityService.approve_compatibility(
                compatibility_id=compatibility.id,
            )

    def test_reject_pending_compatibility(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = (
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )
        )

        rejected = (
            CompatibilityService.reject_compatibility(
                compatibility_id=compatibility.id,
                notes="Vehicle configuration requires verification.",
            )
        )

        assert rejected.status == CompatibilityStatus.REJECTED
        assert rejected.notes == (
            "Vehicle configuration requires verification."
        )

    def test_cannot_reject_already_rejected(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = (
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )
        )

        CompatibilityService.reject_compatibility(
            compatibility_id=compatibility.id,
        )

        with pytest.raises(
            ValueError,
            match="Only pending compatibility can be rejected",
        ):
            CompatibilityService.reject_compatibility(
                compatibility_id=compatibility.id,
            )

    def test_approve_rejects_inactive_product(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = (
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )
        )

        product.is_active = False
        product.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Product is not active"):
            CompatibilityService.approve_compatibility(
                compatibility_id=compatibility.id,
            )

    def test_approve_rejects_inactive_vehicle_variant(
        self,
        product,
        vehicle_variant,
    ):
        compatibility = (
            CompatibilityService.create_compatibility(
                product=product,
                vehicle_variant=vehicle_variant,
            )
        )

        vehicle_variant.is_active = False
        vehicle_variant.save(update_fields=["is_active"])

        with pytest.raises(
            ValueError,
            match="Vehicle variant is not active",
        ):
            CompatibilityService.approve_compatibility(
                compatibility_id=compatibility.id,
            )

    def test_reject_nonexistent_compatibility(self):
        with pytest.raises(
            ValueError,
            match="Compatibility not found",
        ):
            CompatibilityService.reject_compatibility(
                compatibility_id="00000000-0000-0000-0000-000000000000",
            )