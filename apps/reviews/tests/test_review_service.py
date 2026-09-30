from decimal import Decimal
from django.core.exceptions import ValidationError
import pytest

from apps.orders.constants import OrderStatus
from apps.reviews.constants import ReviewStatus
from apps.reviews.models.review import Review
from apps.reviews.services.review import ReviewService


@pytest.mark.django_db
class TestReviewService:

    def test_create_store_review(
        self,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = ReviewService.create(
            order_id=order.id,
            customer=customer,
            store_id=active_store.id,
            rating=5,
            comment="  Excellent service.  ",
        )

        assert review.pk is not None
        assert review.order_id == order.id
        assert review.customer_id == customer.id
        assert review.store_id == active_store.id
        assert review.product_id is None
        assert review.rating == 5
        assert review.comment == "Excellent service."
        assert review.status == ReviewStatus.PENDING

    def test_create_product_review(
        self,
        customer,
        active_store,
        order,
        seller_product,
        review_order_item,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = ReviewService.create(
            order_id=order.id,
            customer=customer,
            store_id=active_store.id,
            product_id=seller_product.product_id,
            rating=4,
            comment="Good product.",
        )

        assert review.pk is not None
        assert review.product_id == seller_product.product_id
        assert review.rating == 4

    def test_cannot_review_undelivered_order(
        self,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.ACCEPTED
        order.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Reviews can only be created for delivered orders",
        ):
            ReviewService.create(
                order_id=order.id,
                customer=customer,
                store_id=active_store.id,
                rating=5,
            )

    def test_cannot_review_order_owned_by_another_customer(
        self,
        another_customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Customer must be the owner of the order",
        ):
            ReviewService.create(
                order_id=order.id,
                customer=another_customer,
                store_id=active_store.id,
                rating=5,
            )

    def test_cannot_review_with_wrong_store(
        self,
        customer,
        another_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Store must belong to the order",
        ):
            ReviewService.create(
                order_id=order.id,
                customer=customer,
                store_id=another_store.id,
                rating=5,
            )

    def test_cannot_review_product_not_in_order(
        self,
        customer,
        active_store,
        order,
        active_product,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Product must belong to the order and its store",
        ):
            ReviewService.create(
                order_id=order.id,
                customer=customer,
                store_id=active_store.id,
                product_id=active_product.id,
                rating=5,
            )

    @pytest.mark.parametrize("rating", [0, 6])
    def test_invalid_rating_is_rejected(
        self,
        customer,
        active_store,
        order,
        rating,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        with pytest.raises(ValidationError):
            ReviewService.create(
                order_id=order.id,
                customer=customer,
                store_id=active_store.id,
                rating=rating,
            )

    def test_duplicate_store_review_is_rejected(
        self,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        ReviewService.create(
            order_id=order.id,
            customer=customer,
            store_id=active_store.id,
            rating=5,
        )

        with pytest.raises(ValidationError):
            ReviewService.create(
                order_id=order.id,
                customer=customer,
                store_id=active_store.id,
                rating=4,
            )

    def test_duplicate_product_review_is_rejected(
        self,
        customer,
        active_store,
        order,
        seller_product,
        review_order_item,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        ReviewService.create(
            order_id=order.id,
            customer=customer,
            store_id=active_store.id,
            product_id=seller_product.product_id,
            rating=5,
        )

        with pytest.raises(ValidationError):
            ReviewService.create(
                order_id=order.id,
                customer=customer,
                store_id=active_store.id,
                product_id=seller_product.product_id,
                rating=4,
            )