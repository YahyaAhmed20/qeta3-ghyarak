import pytest

from apps.orders.constants import OrderStatus
from apps.orders.models.order import Order


@pytest.mark.django_db
class TestOrderModel:
    def test_creates_order_with_default_status(
        self,
        customer,
        active_store,
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

        assert order.id is not None
        assert order.customer_id == customer.id
        assert order.store_id == active_store.id
        assert order.status == OrderStatus.CREATED
        assert order.subtotal == "500.00"
        assert order.seller_discount == "0.00"
        assert order.platform_discount == "0.00"
        assert order.delivery_fee == "50.00"
        assert order.total == "550.00"

    def test_order_number_is_unique_and_generated(
        self,
        customer,
        active_store,
    ):
        order = Order.objects.create(
            customer=customer,
            store=active_store,
            subtotal="100.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="30.00",
            total="130.00",
        )

        assert order.order_number
        assert len(order.order_number) > 0

        assert Order.objects.filter(
            order_number=order.order_number
        ).count() == 1

    def test_order_str_contains_order_number(
        self,
        customer,
        active_store,
    ):
        order = Order.objects.create(
            customer=customer,
            store=active_store,
            subtotal="100.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="30.00",
            total="130.00",
        )

        assert order.order_number in str(order)

    def test_order_amounts_cannot_be_negative(
        self,
        customer,
        active_store,
    ):
        order = Order(
            customer=customer,
            store=active_store,
            subtotal="-100.00",
            seller_discount="0.00",
            platform_discount="0.00",
            delivery_fee="30.00",
            total="-70.00",
        )

        with pytest.raises(Exception):
            order.full_clean()