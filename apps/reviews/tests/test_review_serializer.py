import pytest

from apps.orders.constants import OrderStatus
from apps.reviews.api.serializers import ReviewSerializer
from apps.reviews.services.review import ReviewService


@pytest.mark.django_db
class TestReviewSerializer:

    def test_serializes_store_review(
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

        serializer = ReviewSerializer(review)

        assert serializer.data["id"] == str(review.id)
        assert serializer.data["order"] == order.id
        assert serializer.data["customer_id"] == str(customer.id)
        assert serializer.data["store_id"] == str(active_store.id)
        assert serializer.data["product_id"] is None
        assert serializer.data["rating"] == 5
        assert serializer.data["comment"] == "Excellent service."
        assert serializer.data["status"] == review.status

    def test_serializes_product_review(
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

        serializer = ReviewSerializer(review)

        assert serializer.data["product_id"] == str(
            seller_product.product_id
        )
        assert serializer.data["rating"] == 4

    @pytest.mark.parametrize("rating", [0, 6])
    def test_invalid_rating_is_rejected(
        self,
        rating,
    ):
        serializer = ReviewSerializer(
            data={
                "order": "00000000-0000-0000-0000-000000000000",
                "rating": rating,
                "comment": "Test",
            }
        )

        assert serializer.is_valid() is False
        assert "rating" in serializer.errors

    def test_comment_is_stripped(self):
        serializer = ReviewSerializer(
            data={
                "order": "00000000-0000-0000-0000-000000000000",
                "rating": 5,
                "comment": "  Good service  ",
            }
        )

        # order UUID validation will fail before create,
        # so test the field directly.
        assert serializer.fields["comment"].run_validation(
            "  Good service  "
        ) == "Good service"