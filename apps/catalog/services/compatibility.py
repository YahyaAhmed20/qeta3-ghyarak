from django.db import transaction

from apps.catalog.models import (
    CompatibilityStatus,
    ProductCompatibility,
)


class CompatibilityService:

    @staticmethod
    @transaction.atomic
    def create_compatibility(
        *,
        product,
        vehicle_variant,
        notes="",
    ):
        if not product.is_active:
            raise ValueError("Product is not active.")

        if not vehicle_variant.is_active:
            raise ValueError("Vehicle variant is not active.")

        compatibility = ProductCompatibility(
            product=product,
            vehicle_variant=vehicle_variant,
            status=CompatibilityStatus.PENDING,
            notes=notes,
        )

        compatibility.full_clean()
        compatibility.save()

        return compatibility

    @staticmethod
    @transaction.atomic
    def approve_compatibility(
        *,
        compatibility_id,
    ):
        compatibility = (
            ProductCompatibility.objects
            .select_for_update()
            .select_related("product", "vehicle_variant")
            .filter(id=compatibility_id)
            .first()
        )

        if compatibility is None:
            raise ValueError("Compatibility not found.")

        if compatibility.status != CompatibilityStatus.PENDING:
            raise ValueError(
                "Only pending compatibility can be approved."
            )

        if not compatibility.product.is_active:
            raise ValueError("Product is not active.")

        if not compatibility.vehicle_variant.is_active:
            raise ValueError("Vehicle variant is not active.")

        compatibility.status = CompatibilityStatus.APPROVED
        compatibility.save(
            update_fields=["status", "updated_at"]
        )

        return compatibility

    @staticmethod
    @transaction.atomic
    def reject_compatibility(
        *,
        compatibility_id,
        notes="",
    ):
        compatibility = (
            ProductCompatibility.objects
            .select_for_update()
            .filter(id=compatibility_id)
            .first()
        )

        if compatibility is None:
            raise ValueError("Compatibility not found.")

        if compatibility.status != CompatibilityStatus.PENDING:
            raise ValueError(
                "Only pending compatibility can be rejected."
            )

        compatibility.status = CompatibilityStatus.REJECTED

        if notes:
            compatibility.notes = notes

        compatibility.save(
            update_fields=[
                "status",
                "notes",
                "updated_at",
            ]
        )

        return compatibility