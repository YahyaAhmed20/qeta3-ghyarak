import pytest
from apps.accounts.models import User
from apps.cart.constants import CartStatus
from apps.cart.models import Cart
from apps.cart.selectors.cart import CartSelector


@pytest.mark.django_db
class TestCartSelector:

    def test_returns_active_cart_for_customer(
        self,
        customer,
        active_store,
    ):
        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        result = CartSelector.get_active_cart_for_customer(
            customer=customer,
        )

        assert result is not None
        assert result.id == cart.id

    def test_returns_none_when_customer_has_no_active_cart(
        self,
        customer,
    ):
        result = CartSelector.get_active_cart_for_customer(
            customer=customer,
        )

        assert result is None

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

        result = CartSelector.get_active_cart_for_customer(
            customer=customer,
        )

        assert result is None

    def test_does_not_return_another_customer_cart(
        self,
        customer,
        active_store,
    ):
        other_customer = User.objects.create_user(
            phone="+201001234575",
            role="CUSTOMER",
        )

        other_cart = Cart.objects.create(
            customer=other_customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        result = CartSelector.get_active_cart_for_customer(
            customer=customer,
        )

        assert result is None

    def test_returns_cart_with_related_store_and_items(
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

        from apps.cart.services.cart_item import CartItemService

        CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        result = CartSelector.get_active_cart_for_customer(
            customer=customer,
        )

        assert result.id == cart.id
        assert result.store.id == active_store.id
        assert result.items.count() == 1
        assert (
            result.items.first().seller_product.id
            == seller_product.id
        )