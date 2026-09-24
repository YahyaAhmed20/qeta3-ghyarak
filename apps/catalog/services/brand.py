from django.db import transaction

from apps.catalog.models import Brand


class BrandService:

    @staticmethod
    @transaction.atomic
    def create_brand(
        *,
        name,
        slug,
        description="",
        is_active=True,
    ):
        brand = Brand(
            name=name,
            slug=slug,
            description=description,
            is_active=is_active,
        )

        brand.full_clean()
        brand.save()

        return brand

    @staticmethod
    @transaction.atomic
    def update_brand(
        *,
        brand_id,
        name=None,
        slug=None,
        description=None,
    ):
        brand = (
            Brand.objects
            .select_for_update()
            .filter(id=brand_id)
            .first()
        )

        if brand is None:
            raise ValueError("Brand not found.")

        if name is not None:
            brand.name = name

        if slug is not None:
            brand.slug = slug

        if description is not None:
            brand.description = description

        brand.full_clean()
        brand.save()

        return brand

    @staticmethod
    @transaction.atomic
    def deactivate_brand(*, brand_id):
        brand = (
            Brand.objects
            .select_for_update()
            .filter(id=brand_id)
            .first()
        )

        if brand is None:
            raise ValueError("Brand not found.")

        brand.is_active = False
        brand.save(update_fields=["is_active", "updated_at"])

        return brand

    @staticmethod
    @transaction.atomic
    def activate_brand(*, brand_id):
        brand = (
            Brand.objects
            .select_for_update()
            .filter(id=brand_id)
            .first()
        )

        if brand is None:
            raise ValueError("Brand not found.")

        brand.is_active = True
        brand.save(update_fields=["is_active", "updated_at"])

        return brand