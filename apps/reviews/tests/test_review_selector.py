import pytest

from apps.reviews.models import Review
from apps.reviews.selectors import ReviewSelector
from apps.reviews.services.review import ReviewService
from apps.orders.constants import OrderStatus


@pytest.mark.django_db
class TestReviewSelector:

    def test_get_review(
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
        )

        result = ReviewSelector.get_review(
            review_id=review.id,
        )

        assert result is not None
        assert result.id == review.id
        assert result.customer_id == customer.id
        assert result.store_id == active_store.id

    def test_get_review_returns_none_for_invalid_id(self):
        result = ReviewSelector.get_review(
            review_id="00000000-0000-0000-0000-000000000000",
        )

        assert result is None

    def test_get_customer_reviews(
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
        )

        results = ReviewSelector.get_customer_reviews(
            customer_id=customer.id,
        )

        assert results.count() == 1
        assert results.first().id == review.id

    def test_get_store_reviews(
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
            rating=4,
        )

        results = ReviewSelector.get_store_reviews(
            store_id=active_store.id,
        )

        assert results.count() == 1
        assert results.first().id == review.id

    def test_get_product_reviews(
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
            rating=5,
        )

        results = ReviewSelector.get_product_reviews(
            product_id=seller_product.product_id,
        )

        assert results.count() == 1
        assert results.first().id == review.id

    def test_get_order_reviews(
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
        )

        results = ReviewSelector.get_order_reviews(
            order_id=order.id,
        )

        assert results.count() == 1
        assert results.first().id == review.id