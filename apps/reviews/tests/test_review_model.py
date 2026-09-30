import pytest
from django.core.exceptions import ValidationError

from apps.orders.constants import OrderStatus
from apps.reviews.constants import ReviewStatus
from apps.reviews.models.review import Review


@pytest.mark.django_db
class TestReviewModel:

    def test_valid_store_review(
        self,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=customer,
            store=active_store,
            rating=5,
            comment="Excellent service.",
        )

        review.full_clean()

    def test_valid_product_review(
        self,
        customer,
        active_store,
        order,
        seller_product,
        review_order_item,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=customer,
            store=active_store,
            product=seller_product.product,
            rating=4,
            comment="Good product.",
        )

        review.full_clean()

    def test_customer_must_own_order(
        self,
        another_customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=another_customer,
            store=active_store,
            rating=5,
        )

        with pytest.raises(
            ValidationError,
            match="Customer must be the owner of the order",
        ):
            review.full_clean()

    def test_store_must_belong_to_order(
        self,
        customer,
        active_store,
        another_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=customer,
            store=another_store,
            rating=5,
        )

        with pytest.raises(
            ValidationError,
            match="Store must belong to the order",
        ):
            review.full_clean()

    def test_only_customer_can_create_review(
        self,
        finance_owner,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=finance_owner,
            store=active_store,
            rating=5,
        )

        with pytest.raises(
            ValidationError,
            match="Only customers can create reviews",
        ):
            review.full_clean()

    def test_order_must_be_delivered(
        self,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.ACCEPTED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=customer,
            store=active_store,
            rating=5,
        )

        with pytest.raises(
            ValidationError,
            match="Reviews can only be created for delivered orders",
        ):
            review.full_clean()

    def test_product_must_exist_in_order(
        self,
        customer,
        active_store,
        order,
        active_product,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=customer,
            store=active_store,
            product=active_product,
            rating=5,
        )

        with pytest.raises(
            ValidationError,
            match="Product must belong to the order",
        ):
            review.full_clean()

    def test_rating_below_one_is_invalid(
        self,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=customer,
            store=active_store,
            rating=0,
        )

        with pytest.raises(ValidationError):
            review.full_clean()

    def test_rating_above_five_is_invalid(
        self,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=customer,
            store=active_store,
            rating=6,
        )

        with pytest.raises(ValidationError):
            review.full_clean()

    def test_comment_can_be_empty(
        self,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        review = Review(
            order=order,
            customer=customer,
            store=active_store,
            rating=5,
            comment="",
        )

        review.full_clean()

    def test_default_status_is_pending(
        self,
        customer,
        active_store,
        order,
    ):
        review = Review(
            order=order,
            customer=customer,
            store=active_store,
            rating=5,
        )

        assert review.status == ReviewStatus.PENDING