import pytest

from rest_framework.test import APIClient

from apps.orders.constants import OrderStatus
from apps.reviews.services.review import ReviewService


@pytest.mark.django_db
class TestReviewAPI:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_create_store_review(
        self,
        api_client,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])


        api_client.force_authenticate(user=customer)

        response = api_client.post(
            "/api/reviews/",
            {
                "order": str(order.id),
                "store_id": str(active_store.id),
                "rating": 5,
                "comment": "  Excellent service.  ",
            },
            format="json",
        )


        assert response.status_code == 201
        assert response.data["order"] == order.id
        assert response.data["customer_id"] == str(customer.id)
        assert response.data["store_id"] == str(active_store.id)
        assert response.data["product_id"] is None
        assert response.data["rating"] == 5
        assert response.data["comment"] == "Excellent service."

    def test_create_product_review(
        self,
        api_client,
        customer,
        active_store,
        order,
        seller_product,
        review_order_item,
    ):
        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

     

        api_client.force_authenticate(user=customer)

        response = api_client.post(
            "/api/reviews/",
            {
                "order": str(order.id),
                "store_id": str(active_store.id),
                "product_id": str(seller_product.product_id),
                "rating": 4,
                "comment": "Good product.",
            },
            format="json",
        )


        assert response.status_code == 201
        assert response.data["product_id"] == str(seller_product.product_id)
        assert response.data["rating"] == 4

    def test_create_review_requires_authentication(
        self,
        api_client,
        order,
        active_store,
    ):
        response = api_client.post(
            "/api/reviews/",
            {
                "order": str(order.id),
                "store_id": str(active_store.id),
                "rating": 5,
            },
            format="json",
        )

        assert response.status_code == 401

    def test_create_review_rejects_undelivered_order(
        self,
        api_client,
        customer,
        active_store,
        order,
    ):
        order.status = OrderStatus.ACCEPTED
        order.save(update_fields=["status"])

        api_client.force_authenticate(user=customer)

        response = api_client.post(
            "/api/reviews/",
            {
                "order": str(order.id),
                "store_id": str(active_store.id),
                "rating": 5,
            },
            format="json",
        )

        assert response.status_code == 400
        assert "delivered" in response.data["detail"]

    def test_get_review(
        self,
        api_client,
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
            comment="Excellent.",
        )

        api_client.force_authenticate(user=customer)

        response = api_client.get(
            f"/api/reviews/{review.id}/",
        )

        assert response.status_code == 200
        assert response.data["id"] == str(review.id)
        assert response.data["order"] == order.id
        assert response.data["customer_id"] == str(customer.id)
        assert response.data["store_id"] == str(active_store.id)
        assert response.data["rating"] == 5
        assert response.data["comment"] == "Excellent."

    def test_get_review_requires_authentication(
        self,
        api_client,
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

        response = api_client.get(
            f"/api/reviews/{review.id}/",
        )

        assert response.status_code == 401

    def test_get_nonexistent_review_returns_404(
        self,
        api_client,
        customer,
    ):
        api_client.force_authenticate(user=customer)

        response = api_client.get(
            "/api/reviews/00000000-0000-0000-0000-000000000000/",
        )

        assert response.status_code == 404