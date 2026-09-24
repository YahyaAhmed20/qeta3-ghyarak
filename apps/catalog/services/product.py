from django.db import transaction

from apps.catalog.models import Brand, Category, Product, ProductType

class ProductService:

    @staticmethod
    @transaction.atomic
    def create_product(
        *,
        category,
        name,
        slug,
        brand=None,
        description="",
        product_type=ProductType.AFTERMARKET,
        country_of_origin="",
        warranty="",
        is_active=True,
    ):
        if not category.is_active:
            raise ValueError("Category is not active.")

        if brand is not None and not brand.is_active:
            raise ValueError("Brand is not active.")

        product = Product(
            category=category,
            brand=brand,
            name=name,
            slug=slug,
            description=description,
            product_type=product_type,
            country_of_origin=country_of_origin,
            warranty=warranty,
            is_active=is_active,
        )

        product.full_clean()
        product.save()

        return product

    @staticmethod
    @transaction.atomic
    def update_product(
        *,
        product_id,
        category=None,
        brand=None,
        name=None,
        slug=None,
        description=None,
        product_type=None,
        country_of_origin=None,
        warranty=None,
        is_active=None,
    ):
        product = (
            Product.objects
            .select_for_update()
            .filter(id=product_id)
            .first()
        )

        if product is None:
            raise ValueError("Product not found.")

        if category is not None:
            if not category.is_active:
                raise ValueError("Category is not active.")
            product.category = category

        if brand is not None:
            if not brand.is_active:
                raise ValueError("Brand is not active.")
            product.brand = brand

        if name is not None:
            product.name = name

        if slug is not None:
            product.slug = slug

        if description is not None:
            product.description = description

        if product_type is not None:
            product.product_type = product_type

        if country_of_origin is not None:
            product.country_of_origin = country_of_origin

        if warranty is not None:
            product.warranty = warranty

        if is_active is not None:
            product.is_active = is_active

        product.full_clean()
        product.save()

        return product

    @staticmethod
    @transaction.atomic
    def deactivate_product(*, product_id):
        product = (
            Product.objects
            .select_for_update()
            .filter(id=product_id)
            .first()
        )

        if product is None:
            raise ValueError("Product not found.")

        product.is_active = False
        product.save(update_fields=["is_active", "updated_at"])

        return product

    @staticmethod
    @transaction.atomic
    def activate_product(*, product_id):
        product = (
            Product.objects
            .select_for_update()
            .filter(id=product_id)
            .first()
        )

        if product is None:
            raise ValueError("Product not found.")

        product.is_active = True
        product.save(update_fields=["is_active", "updated_at"])

        return product