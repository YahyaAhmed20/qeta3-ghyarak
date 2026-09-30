from django.db import transaction

from apps.orders.constants import OrderStatus
from apps.orders.models import Order, OrderItem
from apps.reviews.models import Review


class ReviewService:

    @staticmethod
    @transaction.atomic
    def create(
        *,
        order_id,
        customer,
        store_id,
        rating,
        product_id=None,
        comment="",
    ):
        order = (
            Order.objects
            .select_for_update()
            .select_related("store", "customer")
            .get(id=order_id)
        )

        if order.status != OrderStatus.DELIVERED:
            raise ValueError(
                "Reviews can only be created for delivered orders."
            )

        if order.customer_id != customer.id:
            raise ValueError(
                "Customer must be the owner of the order."
            )

        if order.store_id != store_id:
            raise ValueError(
                "Store must belong to the order."
            )

        if product_id is not None:
            product_exists = OrderItem.objects.filter(
                order_id=order.id,
                seller_product__product_id=product_id,
                seller_product__store_id=order.store_id,
            ).exists()

            if not product_exists:
                raise ValueError(
                    "Product must belong to the order and its store."
                )

        review = Review(
            order=order,
            customer=customer,
            store_id=store_id,
            product_id=product_id,
            rating=rating,
            comment=comment.strip(),
        )

        review.full_clean()
        review.save()

        return review