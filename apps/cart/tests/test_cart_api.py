import pytest
from rest_framework.test import APIClient
from decimal import Decimal
from apps.cart.models import Cart
from apps.cart.constants import CartStatus
from apps.cart.services.cart_item import CartItemService


@pytest.mark.django_db
class TestActiveCartAPI:

    def test_unauthenticated_user_cannot_access_cart(self):
        client = APIClient()

        response = client.get("/api/v1/cart/")

        assert response.status_code == 401

    def test_returns_cart_for_authenticated_customer(
        self,
        customer,
        active_store,
        seller_product,
    ):
        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.get("/api/v1/cart/")

        assert response.status_code == 200
        assert response.data["cart"]["id"] == str(cart.id)
        assert response.data["cart"]["store"] == cart.store_id
        assert response.data["cart"]["status"] == "ACTIVE"
        assert response.data["cart"]["items_count"] == 1
        assert response.data["cart"]["subtotal"] == Decimal("500.00")

    def test_returns_null_when_customer_has_no_cart(
        self,
        customer,
    ):
        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.get("/api/v1/cart/")

        assert response.status_code == 200
        assert response.data == {
            "cart": None,
        }

    def test_does_not_return_another_customer_cart(
        self,
        customer,
        active_store,
    ):
        other_customer = type(customer).objects.create_user(
            phone="+201001234576",
            role="CUSTOMER",
        )

        other_cart = Cart.objects.create(
            customer=other_customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.get("/api/v1/cart/")

        assert response.status_code == 200
        assert response.data == {
            "cart": None,
        }

        assert response.data.get("cart") != str(other_cart.id)

    def test_does_not_return_converted_cart(
        self,
        customer,
        active_store,
    ):
        Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.CONVERTED,
        )

        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.get("/api/v1/cart/")

        assert response.status_code == 200
        assert response.data == {
            "cart": None,
        }