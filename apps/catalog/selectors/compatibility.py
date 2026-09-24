from apps.catalog.models import (
    CompatibilityStatus,
    ProductCompatibility,
)


class CompatibilitySelector:

    @staticmethod
    def get_approved_for_product(*, product_id):
        return (
            ProductCompatibility.objects
            .filter(
                product_id=product_id,
                status=CompatibilityStatus.APPROVED,
                product__is_active=True,
                vehicle_variant__is_active=True,
            )
            .select_related(
                "product",
                "vehicle_variant",
                "vehicle_variant__engine",
                "vehicle_variant__engine__generation",
                "vehicle_variant__engine__generation__model",
                "vehicle_variant__engine__generation__model__make",
            )
        )

    @staticmethod
    def get_approved_for_vehicle(*, vehicle_variant_id):
        return (
            ProductCompatibility.objects
            .filter(
                vehicle_variant_id=vehicle_variant_id,
                status=CompatibilityStatus.APPROVED,
                product__is_active=True,
                vehicle_variant__is_active=True,
            )
            .select_related(
                "product",
                "product__category",
                "product__brand",
                "vehicle_variant",
            )
        )

    @staticmethod
    def get_approved_compatibility(*, compatibility_id):
        return (
            ProductCompatibility.objects
            .filter(
                id=compatibility_id,
                status=CompatibilityStatus.APPROVED,
                product__is_active=True,
                vehicle_variant__is_active=True,
            )
            .select_related(
                "product",
                "product__category",
                "product__brand",
                "vehicle_variant",
                "vehicle_variant__engine",
                "vehicle_variant__engine__generation",
                "vehicle_variant__engine__generation__model",
                "vehicle_variant__engine__generation__model__make",
            )
            .first()
        )