import pytest

from apps.cart.constants import CartStatus
from apps.orders.services.order import OrderService


@pytest.mark.django_db
class TestOrderService:
    def test_rejects_cart_belonging_to_another_customer(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.accounts.models import User
        from apps.cart.models.cart import Cart

        another_customer = User.objects.create_user(
            phone="+201001234570",
            role="CUSTOMER",
        )

        cart = Cart.objects.create(
            customer=another_customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        with pytest.raises(ValueError, match="Cart does not belong to customer"):
            OrderService.create_order(
                customer=customer,
                cart=cart,
                address_snapshot={"city": "Suez"},
            )

    def test_rejects_inactive_cart(
        self,
        customer,
        active_store,
    ):
        from apps.cart.models.cart import Cart

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.CONVERTED,
        )

        with pytest.raises(ValueError, match="Cart is not active"):
            OrderService.create_order(
                customer=customer,
                cart=cart,
                address_snapshot={"city": "Suez"},
            )

    def test_rejects_empty_cart(
        self,
        customer,
        active_store,
    ):
        from apps.cart.models.cart import Cart

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        with pytest.raises(ValueError, match="Cart is empty"):
            OrderService.create_order(
                customer=customer,
                cart=cart,
                address_snapshot={"city": "Suez"},
            )

    def test_rejects_cart_with_inactive_seller_product(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
            unit_price="250.00",
        )

        seller_product.is_active = False
        seller_product.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="Seller product is inactive"):
            OrderService.create_order(
                customer=customer,
                cart=cart,
                address_snapshot={"city": "Suez"},
            )

    def test_rejects_stale_cart_price(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
            unit_price="250.00",
        )

        seller_product.price = "300.00"
        seller_product.save(update_fields=["price"])

        with pytest.raises(ValueError, match="Cart item price is outdated"):
            OrderService.create_order(
                customer=customer,
                cart=cart,
                address_snapshot={"city": "Suez"},
            )

    def test_rejects_insufficient_inventory(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=5,
            unit_price="250.00",
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=2,
            reserved=0,
        )

        with pytest.raises(ValueError, match="Insufficient inventory"):
            OrderService.create_order(
                customer=customer,
                cart=cart,
                address_snapshot={"city": "Suez"},
            )

    def test_reserves_inventory_when_creating_order(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
            unit_price="250.00",
        )

        inventory = Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        # مؤقتًا نتحقق من السلوك المطلوب بعد create_order
        order = OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={"city": "Suez"},
        )

        inventory.refresh_from_db()

        assert inventory.reserved == 2
        assert inventory.available == 8

    def test_creates_order_from_cart(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory
        from apps.orders.models import Order

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
            unit_price="250.00",
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        order = OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={"city": "Suez"},
        )

        assert order.customer_id == customer.id
        assert order.store_id == active_store.id
        assert order.subtotal == 500
        assert order.delivery_fee == 0
        assert order.total == 500

    def test_converts_cart_after_creating_order(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
            unit_price="250.00",
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={"city": "Suez"},
        )

        cart.refresh_from_db()

        assert cart.status == CartStatus.CONVERTED

    def test_checkout_rolls_back_inventory_when_order_creation_fails(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from unittest.mock import patch

        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
            unit_price="250.00",
        )

        inventory = Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        with patch(
            "apps.orders.services.order.OrderItem.objects.create",
            side_effect=RuntimeError("Simulated OrderItem failure"),
        ):
            with pytest.raises(RuntimeError, match="Simulated OrderItem failure"):
                OrderService.create_order(
                    customer=customer,
                    cart=cart,
                    address_snapshot={"city": "Suez"},
                )

        inventory.refresh_from_db()
        cart.refresh_from_db()

        assert inventory.reserved == 0
        assert cart.status == CartStatus.ACTIVE

    def test_order_item_keeps_product_name_snapshot(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory
        from apps.orders.models import OrderItem

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
            unit_price="250.00",
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        order = OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={"city": "Suez"},
        )

        item = OrderItem.objects.get(order=order)

        assert item.product_name_snapshot == "Bosch Oil Filter"

        seller_product.product.name = "Updated Oil Filter"
        seller_product.product.save(update_fields=["name"])

        item.refresh_from_db()

        assert item.product_name_snapshot == "Bosch Oil Filter"

    def test_uses_oem_part_number_in_order_item_snapshot(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.catalog.models import ProductPartNumber
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory
        from apps.orders.models import OrderItem

        ProductPartNumber.objects.create(
            product=seller_product.product,
            part_number="OEM-12345",
            normalized_part_number="OEM12345",
            number_type="OEM",
            is_active=True,
        )

        ProductPartNumber.objects.create(
            product=seller_product.product,
            part_number="AFTER-999",
            normalized_part_number="AFTER999",
            number_type="AFTERMARKET",
            is_active=True,
        )

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
            unit_price="250.00",
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        order = OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={"city": "Suez"},
        )

        item = OrderItem.objects.get(order=order)

        assert item.part_number_snapshot == "OEM-12345"

    def test_falls_back_to_manufacturer_part_number(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.catalog.models import ProductPartNumber
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory
        from apps.orders.models import OrderItem

        ProductPartNumber.objects.create(
            product=seller_product.product,
            part_number="MFR-12345",
            normalized_part_number="MFR12345",
            number_type="MANUFACTURER",
            is_active=True,
        )

        ProductPartNumber.objects.create(
            product=seller_product.product,
            part_number="AFTER-999",
            normalized_part_number="AFTER999",
            number_type="AFTERMARKET",
            is_active=True,
        )

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
            unit_price="250.00",
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        order = OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={"city": "Suez"},
        )

        item = OrderItem.objects.get(order=order)

        assert item.part_number_snapshot == "MFR-12345"

    def test_oem_has_priority_over_other_part_numbers(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.catalog.models import ProductPartNumber
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory
        from apps.orders.models import OrderItem

        ProductPartNumber.objects.create(
            product=seller_product.product,
            part_number="MFR-12345",
            normalized_part_number="MFR12345",
            number_type="MANUFACTURER",
            is_active=True,
        )

        ProductPartNumber.objects.create(
            product=seller_product.product,
            part_number="AFTER-999",
            normalized_part_number="AFTER999",
            number_type="AFTERMARKET",
            is_active=True,
        )

        ProductPartNumber.objects.create(
            product=seller_product.product,
            part_number="OEM-77777",
            normalized_part_number="OEM77777",
            number_type="OEM",
            is_active=True,
        )

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
            unit_price="250.00",
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        order = OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={"city": "Suez"},
        )

        item = OrderItem.objects.get(order=order)

        assert item.part_number_snapshot == "OEM-77777"

    def test_cannot_checkout_same_cart_twice(
        self,
        customer,
        active_store,
        seller_product,
    ):
        from apps.cart.models.cart import Cart
        from apps.cart.models.item import CartItem
        from apps.inventory.models.inventory import Inventory

        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
            status=CartStatus.ACTIVE,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=1,
            unit_price="250.00",
        )

        Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={"city": "Suez"},
        )

        cart.refresh_from_db()

        with pytest.raises(ValueError, match="Cart is not active"):
            OrderService.create_order(
                customer=customer,
                cart=cart,
                address_snapshot={"city": "Suez"},
            )