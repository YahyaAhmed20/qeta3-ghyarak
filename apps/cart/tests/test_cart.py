import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal

from apps.accounts.models import User
from apps.cart.constants import CartStatus
from apps.cart.models import Cart, CartItem
from apps.stores.models import Store, StoreStatus, SellerProduct


@pytest.mark.django_db
class TestCartModel:

    def test_create_active_cart(
        self,
        customer,
        active_store,
    ):
        cart = Cart(
            customer=customer,
            store=active_store,
        )

        cart.full_clean()
        cart.save()

        assert cart.status == CartStatus.ACTIVE
        assert cart.customer == customer
        assert cart.store == active_store

    def test_non_customer_cannot_have_cart(
        self,
        seller_owner,
        active_store,
    ):
        cart = Cart(
            customer=seller_owner,
            store=active_store,
        )

        with pytest.raises(ValidationError) as exc:
            cart.full_clean()

        assert "customer" in exc.value.message_dict

    def test_inactive_store_cannot_have_cart(
        self,
        customer,
        inactive_store,
    ):
        cart = Cart(
            customer=customer,
            store=inactive_store,
        )

        with pytest.raises(ValidationError) as exc:
            cart.full_clean()

        assert "store" in exc.value.message_dict

    def test_unverified_store_cannot_have_cart(
        self,
        customer,
        unverified_store,
    ):
        cart = Cart(
            customer=customer,
            store=unverified_store,
        )

        with pytest.raises(ValidationError) as exc:
            cart.full_clean()

        assert "store" in exc.value.message_dict

    def test_customer_can_have_only_one_active_cart(
        self,
        customer,
        active_store,
    ):
        Cart.objects.create(
            customer=customer,
            store=active_store,
        )

        with pytest.raises(IntegrityError):
            Cart.objects.create(
                customer=customer,
                store=active_store,
            )

    def test_customer_can_create_new_cart_after_conversion(
        self,
        customer,
        active_store,
    ):
        first_cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.CONVERTED,
        )

        second_cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        assert first_cart.status == CartStatus.CONVERTED
        assert second_cart.status == CartStatus.ACTIVE
        assert second_cart.customer == customer


@pytest.mark.django_db
class TestCartItemModel:

    def test_create_cart_item(
        self,
        cart,
        seller_product,
    ):
        item = CartItem(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
            unit_price=Decimal("250.00"),
        )

        item.full_clean()
        item.save()

        assert item.quantity == 2
        assert item.unit_price == Decimal("250.00")
        assert item.subtotal == Decimal("500.00")

    def test_quantity_must_be_positive(
        self,
        cart,
        seller_product,
    ):
        item = CartItem(
            cart=cart,
            seller_product=seller_product,
            quantity=0,
            unit_price=Decimal("250.00"),
        )

        with pytest.raises(ValidationError) as exc:
            item.full_clean()

        assert "quantity" in exc.value.message_dict

    def test_unit_price_must_be_positive(
        self,
        cart,
        seller_product,
    ):
        item = CartItem(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
            unit_price=Decimal("0.00"),
        )

        with pytest.raises(ValidationError) as exc:
            item.full_clean()

        assert "unit_price" in exc.value.message_dict

    def test_product_must_belong_to_cart_store(
        self,
        cart,
        active_product,
        db,
    ):
        other_owner = User.objects.create_user(
            phone="+201001234570",
            role="SELLER_OWNER",
        )

        other_store = Store.objects.create(
            owner=other_owner,
            name="Other Store",
            slug="other-store-cart",
            phone="+201001234570",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        other_seller_product = SellerProduct.objects.create(
            store=other_store,
            product=active_product,
            price="300.00",
            is_active=True,
        )

        item = CartItem(
            cart=cart,
            seller_product=other_seller_product,
            quantity=1,
            unit_price=Decimal("300.00"),
        )

        with pytest.raises(ValidationError) as exc:
            item.full_clean()

        assert "seller_product" in exc.value.message_dict

    def test_inactive_seller_product_cannot_be_added(
        self,
        cart,
        seller_product,
    ):
        seller_product.is_active = False
        seller_product.save(update_fields=["is_active"])

        item = CartItem(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
            unit_price=Decimal("250.00"),
        )

        with pytest.raises(ValidationError) as exc:
            item.full_clean()

        assert "seller_product" in exc.value.message_dict

    def test_same_product_cannot_be_added_twice(
        self,
        cart,
        seller_product,
    ):
        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
            unit_price=Decimal("250.00"),
        )

        with pytest.raises(IntegrityError):
            CartItem.objects.create(
                cart=cart,
                seller_product=seller_product,
                quantity=2,
                unit_price=Decimal("250.00"),
            )