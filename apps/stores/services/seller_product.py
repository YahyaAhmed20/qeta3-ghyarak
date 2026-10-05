from django.db import transaction

from apps.stores.models import SellerProduct

_UNSET = object()


class SellerProductService:

    @staticmethod
    @transaction.atomic
    def create_seller_product(
        *,
        store,
        product,
        price,
        sale_price=None,
        seller_sku="",
    ):
        if not store.is_verified or store.status != "ACTIVE":
            raise ValueError(
                "Store must be active and verified."
            )

        if not product.is_active:
            raise ValueError(
                "Product is not active."
            )

        if SellerProduct.objects.filter(
            store=store,
            product=product,
        ).exists():
            raise ValueError(
                "This product is already listed by this store."
            )

        seller_product = SellerProduct(
            store=store,
            product=product,
            price=price,
            sale_price=sale_price,
            seller_sku=seller_sku,
        )

        seller_product.full_clean()
        seller_product.save()

        return seller_product

    @staticmethod
    @transaction.atomic
    def update_seller_product(
        *,
        seller_product_id,
        store,
        price=None,
        sale_price=_UNSET,
        seller_sku=None,
    ):
        seller_product = (
            SellerProduct.objects
            .select_for_update()
            .filter(
                id=seller_product_id,
                store=store,
            )
            .first()
        )

        if seller_product is None:
            raise ValueError("Seller product not found.")

        if not store.is_verified or store.status != "ACTIVE":
            raise ValueError(
                "Store must be active and verified."
            )

        if price is not None:
            seller_product.price = price

        if sale_price is not _UNSET:
            seller_product.sale_price = sale_price

        if seller_sku is not None:
            seller_product.seller_sku = seller_sku

        seller_product.full_clean()
        seller_product.save()

        return seller_product

    @staticmethod
    @transaction.atomic
    def deactivate_seller_product(
        *,
        seller_product_id,
        store,
    ):
        seller_product = (
            SellerProduct.objects
            .select_for_update()
            .filter(
                id=seller_product_id,
                store=store,
            )
            .first()
        )

        if seller_product is None:
            raise ValueError("Seller product not found.")

        if not seller_product.is_active:
            raise ValueError(
                "Seller product is already inactive."
            )

        seller_product.is_active = False

        seller_product.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return seller_product

    @staticmethod
    @transaction.atomic
    def activate_seller_product(
        *,
        seller_product_id,
        store,
    ):
        seller_product = (
            SellerProduct.objects
            .select_for_update()
            .filter(
                id=seller_product_id,
                store=store,
            )
            .first()
        )

        if seller_product is None:
            raise ValueError("Seller product not found.")

        if seller_product.is_active:
            raise ValueError(
                "Seller product is already active."
            )

        if not store.is_verified or store.status != "ACTIVE":
            raise ValueError(
                "Store must be active and verified."
            )

        if not seller_product.product.is_active:
            raise ValueError(
                "Product is not active."
            )

        seller_product.is_active = True

        seller_product.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return seller_product

    @staticmethod
    @transaction.atomic
    def create_seller_product_with_inventory(
        *,
        store,
        product,
        price,
        sale_price=None,
        seller_sku="",
        initial_stock=0,
        user=None,
    ):
        if initial_stock < 0:
            raise ValueError(
                "Initial stock cannot be negative."
            )

        seller_product = SellerProductService.create_seller_product(
            store=store,
            product=product,
            price=price,
            sale_price=sale_price,
            seller_sku=seller_sku,
        )

        from apps.inventory.models import Inventory

        inventory = Inventory.objects.create(
            seller_product=seller_product,
            on_hand=0,
            reserved=0,
        )

        if initial_stock > 0:
            from apps.inventory.services.inventory import InventoryService

            inventory = InventoryService.restock(
                inventory_id=inventory.id,
                quantity=initial_stock,
                user=user,
                note="Initial stock when seller product was created.",
            )

        return seller_product, inventory