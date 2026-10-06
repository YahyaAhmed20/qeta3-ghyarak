from apps.orders.models import Order


class OrderSelector:

    @staticmethod
    def get_store_orders(*, store):
        return (
            Order.objects
            .filter(store=store)
            .select_related(
                "customer",
                "store",
            )
            .prefetch_related(
                "items",
                "items__seller_product",
                "items__seller_product__product",
            )
            .order_by("-created_at")
        )

    @staticmethod
    def get_store_order(*, store, order_id):
        return (
            Order.objects
            .filter(
                id=order_id,
                store=store,
            )
            .select_related(
                "customer",
                "store",
            )
            .prefetch_related(
                "items",
                "items__seller_product",
                "items__seller_product__product",
            )
            .first()
        )