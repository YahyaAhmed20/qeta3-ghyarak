import pytest
from decimal import Decimal

from apps.orders.models.item import OrderItem
from apps.orders.models.order import Order
from apps.stores.models.seller_product import SellerProduct


@pytest.mark.django_db
class TestOrderItemModel:
    def test_creates_order_item_with_snapshots(
        self,
        customer,
        active_store,
        seller_product,
    ):
        order = Order.objects.create(
            customer=customer,
            store=active_store,
            subtotal="500.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="50.00",
            total="550.00",
        )

        item = OrderItem.objects.create(
            order=order,
            seller_product=seller_product,
            product_name_snapshot="Bosch Oil Filter",
            part_number_snapshot="0986AF1234",
            unit_price="250.00",
            discount="0.00",
            quantity=2,
        )

        assert item.id is not None
        assert item.order_id == order.id
        assert item.seller_product_id == seller_product.id
        assert item.product_name_snapshot == "Bosch Oil Filter"
        assert item.part_number_snapshot == "0986AF1234"
        assert Decimal(str(item.unit_price)) == Decimal("250.00")
        assert Decimal(str(item.discount)) == Decimal("0.00")
        assert item.quantity == 2
        assert item.subtotal == Decimal("500.00")

    def test_order_item_requires_positive_quantity(
        self,
        customer,
        active_store,
        seller_product,
    ):
        order = Order.objects.create(
            customer=customer,
            store=active_store,
            subtotal="500.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="50.00",
            total="550.00",
        )

        item = OrderItem(
            order=order,
            seller_product=seller_product,
            product_name_snapshot="Bosch Oil Filter",
            part_number_snapshot="0986AF1234",
            unit_price="250.00",
            discount="0.00",
            quantity=0,
        )

        with pytest.raises(Exception):
            item.full_clean()

    def test_order_item_requires_positive_unit_price(
        self,
        customer,
        active_store,
        seller_product,
    ):
        order = Order.objects.create(
            customer=customer,
            store=active_store,
            subtotal="500.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="50.00",
            total="550.00",
        )

        item = OrderItem(
            order=order,
            seller_product=seller_product,
            product_name_snapshot="Bosch Oil Filter",
            part_number_snapshot="0986AF1234",
            unit_price="0.00",
            discount="0.00",
            quantity=2,
        )

        with pytest.raises(Exception):
            item.full_clean()

    def test_order_item_cannot_have_negative_discount(
        self,
        customer,
        active_store,
        seller_product,
    ):
        order = Order.objects.create(
            customer=customer,
            store=active_store,
            subtotal="500.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="50.00",
            total="550.00",
        )

        item = OrderItem(
            order=order,
            seller_product=seller_product,
            product_name_snapshot="Bosch Oil Filter",
            part_number_snapshot="0986AF1234",
            unit_price="250.00",
            discount="-10.00",
            quantity=2,
        )

        with pytest.raises(Exception):
            item.full_clean()

    def test_order_item_belongs_to_same_store_as_order(
        self,
        customer,
        active_store,
        seller_product,
    ):
        order = Order.objects.create(
            customer=customer,
            store=active_store,
            subtotal="500.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="50.00",
            total="550.00",
        )

        item = OrderItem(
            order=order,
            seller_product=seller_product,
            product_name_snapshot="Bosch Oil Filter",
            part_number_snapshot="0986AF1234",
            unit_price="250.00",
            discount="0.00",
            quantity=2,
        )

        item.full_clean()

        assert item.order.store_id == item.seller_product.store_id

    def test_order_item_str_contains_product_name_and_quantity(
        self,
        customer,
        active_store,
        seller_product,
    ):
        order = Order.objects.create(
            customer=customer,
            store=active_store,
            subtotal="250.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="30.00",
            total="280.00",
        )

        item = OrderItem.objects.create(
            order=order,
            seller_product=seller_product,
            product_name_snapshot="Bosch Oil Filter",
            part_number_snapshot="0986AF1234",
            unit_price="250.00",
            discount="0.00",
            quantity=1,
        )

        assert "Bosch Oil Filter" in str(item)
        assert "1" in str(item)