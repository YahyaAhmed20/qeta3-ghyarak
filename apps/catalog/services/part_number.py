from django.db import transaction

from apps.catalog.models import (
    Brand,
    Product,
    ProductPartNumber,
)


class PartNumberService:

    @staticmethod
    @transaction.atomic
    def create_part_number(
        *,
        product,
        part_number,
        number_type,
        brand=None,
        is_active=True,
    ):
        if not product.is_active:
            raise ValueError("Product is not active.")

        if brand is not None and not brand.is_active:
            raise ValueError("Brand is not active.")

        product_part_number = ProductPartNumber(
            product=product,
            brand=brand,
            part_number=part_number,
            number_type=number_type,
            is_active=is_active,
        )

        product_part_number.full_clean()
        product_part_number.save()

        return product_part_number

    @staticmethod
    @transaction.atomic
    def update_part_number(
        *,
        part_number_id,
        product=None,
        brand=None,
        part_number=None,
        number_type=None,
        is_active=None,
    ):
        product_part_number = (
            ProductPartNumber.objects
            .select_for_update()
            .filter(id=part_number_id)
            .first()
        )

        if product_part_number is None:
            raise ValueError("Part number not found.")

        if product is not None:
            if not product.is_active:
                raise ValueError("Product is not active.")

            product_part_number.product = product

        if brand is not None:
            if not brand.is_active:
                raise ValueError("Brand is not active.")

            product_part_number.brand = brand

        if part_number is not None:
            product_part_number.part_number = part_number

        if number_type is not None:
            product_part_number.number_type = number_type

        if is_active is not None:
            product_part_number.is_active = is_active

        product_part_number.full_clean()
        product_part_number.save()

        return product_part_number

    @staticmethod
    @transaction.atomic
    def deactivate_part_number(*, part_number_id):
        product_part_number = (
            ProductPartNumber.objects
            .select_for_update()
            .filter(id=part_number_id)
            .first()
        )

        if product_part_number is None:
            raise ValueError("Part number not found.")

        product_part_number.is_active = False

        product_part_number.save(
            update_fields=["is_active", "updated_at"]
        )

        return product_part_number

    @staticmethod
    @transaction.atomic
    def activate_part_number(*, part_number_id):
        product_part_number = (
            ProductPartNumber.objects
            .select_for_update()
            .filter(id=part_number_id)
            .first()
        )

        if product_part_number is None:
            raise ValueError("Part number not found.")

        if not product_part_number.product.is_active:
            raise ValueError("Product is not active.")

        if (
            product_part_number.brand is not None
            and not product_part_number.brand.is_active
        ):
            raise ValueError("Brand is not active.")

        product_part_number.is_active = True

        product_part_number.save(
            update_fields=["is_active", "updated_at"]
        )

        return product_part_number