from decimal import Decimal

from django.db import transaction

from apps.cart.constants import CartStatus
from apps.cart.models import CartItem
from apps.stores.models import SellerProduct


class CartItemService:

    @staticmethod
    @transaction.atomic
    def add_item(*, cart, seller_product, quantity):
        if cart.status != CartStatus.ACTIVE:
            raise ValueError("Only active carts can be modified.")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        seller_product = (
            SellerProduct.objects
            .select_for_update()
            .select_related("store")
            .get(id=seller_product.id)
        )

        if seller_product.store_id != cart.store_id:
            raise ValueError(
                "Seller product must belong to the same store as the cart."
            )

        if not seller_product.is_active:
            raise ValueError("Seller product must be active.")

        unit_price = (
            seller_product.sale_price
            if seller_product.sale_price is not None
            else seller_product.price
        )

        if unit_price <= Decimal("0.00"):
            raise ValueError("Seller product price must be greater than zero.")

        item = (
            CartItem.objects
            .select_for_update()
            .filter(
                cart=cart,
                seller_product=seller_product,
            )
            .first()
        )

        if item:
            item.quantity += quantity
            item.unit_price = unit_price
            item.save(
                update_fields=[
                    "quantity",
                    "unit_price",
                    "updated_at",
                ]
            )
            return item, False

        item = CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=quantity,
            unit_price=unit_price,
        )

        return item, True

    @staticmethod
    @transaction.atomic
    def update_quantity(*, cart, item_id, quantity):
        if cart.status != CartStatus.ACTIVE:
            raise ValueError("Only active carts can be modified.")

        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        item = (
            CartItem.objects
            .select_for_update()
            .select_related("seller_product", "seller_product__store")
            .filter(
                id=item_id,
                cart=cart,
            )
            .first()
        )

        if item is None:
            raise ValueError("Cart item not found.")

        if item.seller_product.store_id != cart.store_id:
            raise ValueError(
                "Seller product must belong to the same store as the cart."
            )

        if not item.seller_product.is_active:
            raise ValueError("Seller product must be active.")

        item.quantity = quantity
        item.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        return item

    @staticmethod
    @transaction.atomic
    def remove_item(*, cart, item_id):
        if cart.status != CartStatus.ACTIVE:
            raise ValueError("Only active carts can be modified.")

        item = (
            CartItem.objects
            .select_for_update()
            .filter(
                id=item_id,
                cart=cart,
            )
            .first()
        )

        if item is None:
            raise ValueError("Cart item not found.")

        item.delete()

        return True

    @staticmethod
    @transaction.atomic
    def clear_cart(*, cart):
        if cart.status != CartStatus.ACTIVE:
            raise ValueError("Only active carts can be modified.")

        deleted_count, _ = CartItem.objects.filter(
            cart=cart,
        ).delete()

        return deleted_count