from decimal import Decimal

from django.db.migrations import serializer
import pytest

from apps.cart.api.serializers import CartItemSerializer, CartSerializer
from apps.cart.models import CartItem
from apps.cart.services.cart_item import CartItemService


@pytest.mark.django_db
class TestCartItemSerializer:

    def test_serializes_cart_item(
        self,
        cart,
        seller_product,
    ):
        item, _ = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        serializer = CartItemSerializer(item)

        assert serializer.data["id"] == str(item.id)
        assert serializer.data["seller_product_id"] == str(
            seller_product.id
        )
        assert serializer.data["product_name"] == "Bosch Oil Filter"
        assert serializer.data["quantity"] == 2
        assert serializer.data["unit_price"] == "250.00"
        assert serializer.data["subtotal"] == "500.00"

    def test_price_fields_are_read_only(
        self,
        cart,
        seller_product,
    ):
        item, _ = CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
        )

        serializer = CartItemSerializer(
            item,
            data={
                "quantity": 3,
                "unit_price": "1.00",
                "subtotal": "1.00",
            },
            partial=True,
        )

        assert serializer.is_valid()

        assert "unit_price" not in serializer.validated_data
        assert "subtotal" not in serializer.validated_data


@pytest.mark.django_db
class TestCartSerializer:

    def test_serializes_cart_with_items(
        self,
        cart,
        seller_product,
    ):
        CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        serializer = CartSerializer(cart)

        assert serializer.data["id"] == str(cart.id)
        assert serializer.data["store"] == cart.store_id
        assert serializer.data["status"] == "ACTIVE"
        assert serializer.data["items_count"] == 1
        # CartSerializer
        assert serializer.data["subtotal"] == Decimal("500.00")
        assert len(serializer.data["items"]) == 1

    def test_serializes_empty_cart(
        self,
        cart,
    ):
        serializer = CartSerializer(cart)

        assert serializer.data["items"] == []
        assert serializer.data["items_count"] == 0
        assert serializer.data["subtotal"] == Decimal("0.00")

    def test_cart_fields_are_read_only(
        self,
        cart,
    ):
        serializer = CartSerializer(
            cart,
            data={
                "store": str(cart.store_id),
                "status": "CONVERTED",
                "subtotal": "999999.00",
                "items_count": 999,
            },
            partial=True,
        )

        assert serializer.is_valid()

        assert "store" not in serializer.validated_data
        assert "status" not in serializer.validated_data
        assert "subtotal" not in serializer.validated_data
        assert "items_count" not in serializer.validated_data