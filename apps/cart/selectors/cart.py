from apps.cart.constants import CartStatus
from apps.cart.models import Cart


class CartSelector:

    @staticmethod
    def get_active_cart_for_customer(*, customer):
        return (
            Cart.objects
            .select_related("store")
            .prefetch_related(
                "items__seller_product__product",
            )
            .filter(
                customer=customer,
                status=CartStatus.ACTIVE,
            )
            .first()
        )