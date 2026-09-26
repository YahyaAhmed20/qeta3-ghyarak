from decimal import Decimal

from django.db import transaction

from apps.cart.constants import CartStatus
from apps.cart.models import Cart, CartItem
from apps.catalog.models import ProductPartNumber
from apps.inventory.models.inventory import Inventory
from apps.inventory.services.inventory import InventoryService
from apps.orders.constants import OrderStatus
from apps.orders.models import Order, OrderItem
from apps.orders.permissions import validate_actor_permission
from apps.orders.services.state_machine import validate_transition


class OrderService:
    @staticmethod
    @transaction.atomic
    def transition_status(
        *,
        order_id,
        new_status,
        actor,
        delivery_otp_id=None,
    ) -> Order:
        order = (
            Order.objects
            .select_for_update()
            .get(id=order_id)
        )

        validate_transition(
            current_status=order.status,
            new_status=new_status,
        )

        validate_actor_permission(
            actor=actor,
            current_status=order.status,
            new_status=new_status,
        )

        if actor.role in {
            "SELLER_OWNER",
            "SELLER_MANAGER",
            "SELLER_STAFF",
        }:
            if order.store.owner_id != actor.id:
                raise PermissionError(
                    "Actor does not have access to this order."
                )

        if actor.role == "CUSTOMER":
            if order.customer_id != actor.id:
                raise PermissionError(
                    "Actor does not have access to this order."
                )

        if new_status == OrderStatus.CANCELLED:
            for item in order.items.select_related("seller_product"):
                inventory = Inventory.objects.get(
                    seller_product=item.seller_product
                )

                InventoryService.release(
                    inventory_id=inventory.id,
                    quantity=item.quantity,
                )

        if new_status == OrderStatus.DELIVERED:
            if not delivery_otp_id:
                raise ValueError("Delivery OTP is required.")

            from apps.orders.models import DeliveryOTP

            delivery_otp = (
                DeliveryOTP.objects
                .select_for_update()
                .filter(
                    id=delivery_otp_id,
                    order=order,
                )
                .first()
            )

            if delivery_otp is None:
                raise ValueError("Delivery OTP not found.")

            if delivery_otp.status != "VERIFIED":
                raise ValueError("Delivery OTP is not verified.")

            for item in order.items.select_related("seller_product"):
                inventory = Inventory.objects.get(
                    seller_product=item.seller_product
                )

                InventoryService.sell(
                    inventory_id=inventory.id,
                    quantity=item.quantity,
                )

        order.status = new_status
        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return order

    @staticmethod
    @transaction.atomic
    def create_order(
        *,
        customer,
        cart: Cart,
        address_snapshot: dict,
        delivery_fee: Decimal = Decimal("0.00"),
        notes: str = "",
    ) -> Order:
        """
        Create an order from an active cart.

        The complete checkout flow will be implemented incrementally.
        """
        if cart.customer_id != customer.id:
            raise ValueError("Cart does not belong to customer")

        if cart.status != CartStatus.ACTIVE:
            raise ValueError("Cart is not active")

        if not cart.items.exists():
            raise ValueError("Cart is empty")

        cart_items = cart.items.select_related("seller_product").all()

        for cart_item in cart_items:
            if not cart_item.seller_product.is_active:
                raise ValueError("Seller product is inactive")

            current_price = (
                cart_item.seller_product.sale_price
                or cart_item.seller_product.price
            )

            if cart_item.unit_price != current_price:
                raise ValueError("Cart item price is outdated")

            inventory = Inventory.objects.filter(
                seller_product=cart_item.seller_product
            ).first()

            if inventory is None:
                raise ValueError("Inventory not found")

            if inventory.available < cart_item.quantity:
                raise ValueError("Insufficient inventory")

        for cart_item in cart_items:
            inventory = Inventory.objects.get(
                seller_product=cart_item.seller_product
            )

            InventoryService.reserve(
                inventory_id=inventory.id,
                quantity=cart_item.quantity,
            )

        subtotal = sum(
            (
                cart_item.unit_price * cart_item.quantity
                for cart_item in cart_items
            ),
            Decimal("0.00"),
        )

        total = subtotal + delivery_fee

        order = Order.objects.create(
            customer=customer,
            store=cart.store,
            subtotal=subtotal,
            seller_discount=Decimal("0.00"),
            platform_discount=Decimal("0.00"),
            delivery_fee=delivery_fee,
            total=total,
            address_snapshot=address_snapshot,
            notes=notes,
        )

        for cart_item in cart_items:
            part_number = None

            for number_type in (
                "OEM",
                "MANUFACTURER",
                "AFTERMARKET",
                "CROSS_REFERENCE",
            ):
                part_number = (
                    ProductPartNumber.objects
                    .filter(
                        product=cart_item.seller_product.product,
                        is_active=True,
                        number_type=number_type,
                    )
                    .values_list("part_number", flat=True)
                    .first()
                )

                if part_number:
                    break

            OrderItem.objects.create(
                order=order,
                seller_product=cart_item.seller_product,
                product_name_snapshot=cart_item.seller_product.product.name,
                part_number_snapshot=part_number or "",
                unit_price=cart_item.unit_price,
                discount=Decimal("0.00"),
                quantity=cart_item.quantity,
            )

        cart.status = CartStatus.CONVERTED
        cart.save(update_fields=["status", "updated_at"])

        return order