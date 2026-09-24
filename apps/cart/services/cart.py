from django.db import transaction

from apps.cart.constants import CartStatus
from apps.cart.models import Cart


class CartService:

    @staticmethod
    @transaction.atomic
    def get_or_create_active_cart(*, customer, store):
        if customer.role != "CUSTOMER":
            raise ValueError("Only customers can have carts.")

        if store.status != "ACTIVE" or not store.is_verified:
            raise ValueError("Store must be active and verified.")

        cart = (
            Cart.objects
            .select_for_update()
            .filter(
                customer=customer,
                status=CartStatus.ACTIVE,
            )
            .first()
        )

        if cart:
            if cart.store_id != store.id:
                raise ValueError(
                    "Customer already has an active cart for another store."
                )
            return cart, False

        cart = Cart.objects.create(
            customer=customer,
            store=store,
            status=CartStatus.ACTIVE,
        )

        return cart, True