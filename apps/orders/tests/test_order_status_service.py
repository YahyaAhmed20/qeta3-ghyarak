import pytest

from apps.orders.constants import OrderStatus
from apps.orders.services.order import OrderService


@pytest.mark.django_db
def test_transition_status_updates_order(
    order,
    seller_owner,
):
    updated_order = OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.ACCEPTED,
        actor=seller_owner,
    )

    assert updated_order.status == OrderStatus.ACCEPTED

    order.refresh_from_db()

    assert order.status == OrderStatus.ACCEPTED


@pytest.mark.django_db
def test_transition_status_rejects_invalid_transition(
    order,
    customer,
):
    with pytest.raises(ValueError, match="Invalid order transition"):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.DELIVERED,
            actor=customer,
        )


@pytest.mark.django_db
def test_transition_status_raises_for_unknown_order(
    customer,
):
    import uuid

    with pytest.raises(Exception):
        OrderService.transition_status(
            order_id=uuid.uuid4(),
            new_status=OrderStatus.ACCEPTED,
            actor=customer,
        )


@pytest.mark.django_db
def test_seller_cannot_transition_order_from_another_store(
    order,
):
    from apps.accounts.models import User

    another_seller = User.objects.create_user(
        phone="+201001234570",
        role="SELLER_OWNER",
    )

    with pytest.raises(
        PermissionError,
        match="does not have access to this order",
    ):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.ACCEPTED,
            actor=another_seller,
        )


@pytest.mark.django_db
def test_customer_cannot_transition_order_from_another_customer(
    order,
):
    from apps.accounts.models import User

    another_customer = User.objects.create_user(
        phone="+201001234571",
        role="CUSTOMER",
    )

    with pytest.raises(
        PermissionError,
        match="does not have access to this order",
    ):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.CANCELLED,
            actor=another_customer,
        )


@pytest.mark.django_db
def test_admin_can_transition_any_order(
    order,
):
    from apps.accounts.models import User

    admin = User.objects.create_user(
        phone="+201001234572",
        role="ADMIN",
    )

    updated_order = OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.ACCEPTED,
        actor=admin,
    )

    assert updated_order.status == OrderStatus.ACCEPTED


@pytest.mark.django_db
def test_super_admin_can_transition_any_order(
    order,
):
    from apps.accounts.models import User

    super_admin = User.objects.create_user(
        phone="+201001234573",
        role="SUPER_ADMIN",
    )

    updated_order = OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.ACCEPTED,
        actor=super_admin,
    )

    assert updated_order.status == OrderStatus.ACCEPTED


@pytest.mark.django_db
def test_transition_status_does_not_persist_on_failure(
    order,
    seller_owner,
    monkeypatch,
):
    def fail_transition(*, current_status, new_status):
        raise ValueError("Forced failure")

    monkeypatch.setattr(
        "apps.orders.services.order.validate_transition",
        fail_transition,
    )

    with pytest.raises(ValueError, match="Forced failure"):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.ACCEPTED,
            actor=seller_owner,
        )

    order.refresh_from_db()

    assert order.status == OrderStatus.CREATED


@pytest.mark.django_db
def test_cancelling_order_releases_reserved_inventory(
    customer,
    active_store,
    seller_product,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.models import Inventory, InventoryMovement
    from apps.inventory.constants import InventoryMovementType

    # 1. Prepare inventory
    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    # 2. Prepare cart
    cart = Cart.objects.create(
        customer=customer,
        store=active_store,
    )

    CartItem.objects.create(
        cart=cart,
        seller_product=seller_product,
        quantity=3,
        unit_price=Decimal("250.00"),
    )

    # 3. Checkout reserves 3 units
    order = OrderService.create_order(
        customer=customer,
        cart=cart,
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )

    inventory.refresh_from_db()

    assert inventory.on_hand == 10
    assert inventory.reserved == 3
    assert inventory.available == 7

    # 4. Customer cancels the order
    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.CANCELLED,
        actor=customer,
    )

    # 5. Reservation must be released
    inventory.refresh_from_db()
    order.refresh_from_db()

    assert order.status == OrderStatus.CANCELLED
    assert inventory.on_hand == 10
    assert inventory.reserved == 0
    assert inventory.available == 10

    # 6. Verify inventory movement
    assert InventoryMovement.objects.filter(
        inventory=inventory,
        movement_type=InventoryMovementType.RELEASE,
        quantity=3,
    ).count() == 1


@pytest.mark.django_db
def test_cannot_cancel_already_cancelled_order(
    customer,
    active_store,
    seller_product,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.models import Inventory

    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    cart = Cart.objects.create(
        customer=customer,
        store=active_store,
    )

    CartItem.objects.create(
        cart=cart,
        seller_product=seller_product,
        quantity=3,
        unit_price=Decimal("250.00"),
    )

    order = OrderService.create_order(
        customer=customer,
        cart=cart,
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.CANCELLED,
        actor=customer,
    )

    inventory.refresh_from_db()

    assert inventory.reserved == 0

    with pytest.raises(
        ValueError,
        match="Invalid order transition",
    ):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.CANCELLED,
            actor=customer,
        )

    inventory.refresh_from_db()

    assert inventory.reserved == 0


@pytest.mark.django_db
def test_delivering_order_sells_reserved_inventory(
    customer,
    active_store,
    seller_product,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.models import Inventory
    from apps.inventory.constants import InventoryMovementType
    from apps.inventory.models import InventoryMovement

    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    cart = Cart.objects.create(
        customer=customer,
        store=active_store,
    )

    CartItem.objects.create(
        cart=cart,
        seller_product=seller_product,
        quantity=3,
        unit_price=Decimal("250.00"),
    )

    order = OrderService.create_order(
        customer=customer,
        cart=cart,
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )

    inventory.refresh_from_db()

    assert inventory.on_hand == 10
    assert inventory.reserved == 3
    assert inventory.available == 7

    seller_owner = active_store.owner

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.ACCEPTED,
        actor=seller_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.PREPARING,
        actor=seller_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.READY,
        actor=seller_owner,
    )

    delivery_user = type(
        "DeliveryActor",
        (),
        {"role": "DELIVERY", "id": None},
    )()

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.OUT_FOR_DELIVERY,
        actor=delivery_user,
    )

    order.refresh_from_db()

    from apps.orders.services.delivery_otp import DeliveryOTPService

    otp, code = DeliveryOTPService.create(
        order=order,
    )

    verified_otp = DeliveryOTPService.verify(
        order=order,
        otp_id=otp.id,
        code=code,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.DELIVERED,
        actor=delivery_user,
        delivery_otp_id=verified_otp.id,
    )

    inventory.refresh_from_db()

    assert inventory.on_hand == 7
    assert inventory.reserved == 0
    assert inventory.available == 7

    assert InventoryMovement.objects.filter(
        inventory=inventory,
        movement_type=InventoryMovementType.SALE,
        quantity=3,
    ).count() == 1


@pytest.mark.django_db
def test_delivered_inventory_sale_rolls_back_on_failure(
    customer,
    active_store,
    seller_product,
    monkeypatch,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.models import Inventory
    from apps.orders.models import Order
    from apps.orders.constants import OrderStatus
    from apps.orders.services.order import OrderService

    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    cart = Cart.objects.create(
        customer=customer,
        store=active_store,
    )

    CartItem.objects.create(
        cart=cart,
        seller_product=seller_product,
        quantity=3,
        unit_price=Decimal("250.00"),
    )

    order = OrderService.create_order(
        customer=customer,
        cart=cart,
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )

    seller_owner = active_store.owner

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.ACCEPTED,
        actor=seller_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.PREPARING,
        actor=seller_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.READY,
        actor=seller_owner,
    )

    delivery_user = type(
        "DeliveryActor",
        (),
        {"role": "DELIVERY", "id": None},
    )()

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.OUT_FOR_DELIVERY,
        actor=delivery_user,
    )

    order.refresh_from_db()

    from apps.orders.services.delivery_otp import DeliveryOTPService

    otp, code = DeliveryOTPService.create(
        order=order,
    )

    verified_otp = DeliveryOTPService.verify(
        order=order,
        otp_id=otp.id,
        code=code,
    )

    def failing_sell(*args, **kwargs):
        raise RuntimeError("Simulated inventory failure")

    monkeypatch.setattr(
        "apps.orders.services.order.InventoryService.sell",
        failing_sell,
    )

    with pytest.raises(RuntimeError, match="Simulated inventory failure"):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.DELIVERED,
            actor=delivery_user,
            delivery_otp_id=verified_otp.id,
        )

    order.refresh_from_db()
    inventory.refresh_from_db()

    assert order.status == OrderStatus.OUT_FOR_DELIVERY
    assert inventory.on_hand == 10
    assert inventory.reserved == 3
    assert inventory.available == 7


@pytest.mark.django_db
def test_cannot_deliver_order_without_verified_delivery_otp(
    customer,
    active_store,
    seller_product,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.models import Inventory
    from apps.orders.constants import OrderStatus
    from apps.orders.services.order import OrderService

    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    cart = Cart.objects.create(
        customer=customer,
        store=active_store,
    )

    CartItem.objects.create(
        cart=cart,
        seller_product=seller_product,
        quantity=3,
        unit_price=Decimal("250.00"),
    )

    order = OrderService.create_order(
        customer=customer,
        cart=cart,
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )

    seller_owner = active_store.owner

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.ACCEPTED,
        actor=seller_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.PREPARING,
        actor=seller_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.READY,
        actor=seller_owner,
    )

    delivery_user = type(
        "DeliveryActor",
        (),
        {"role": "DELIVERY", "id": None},
    )()

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.OUT_FOR_DELIVERY,
        actor=delivery_user,
    )

    with pytest.raises(
        ValueError,
        match="Delivery OTP is required",
    ):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.DELIVERED,
            actor=delivery_user,
        )

    order.refresh_from_db()
    inventory.refresh_from_db()

    assert order.status == OrderStatus.OUT_FOR_DELIVERY
    assert inventory.on_hand == 10
    assert inventory.reserved == 3
    assert inventory.available == 7


@pytest.mark.django_db
def test_verified_delivery_otp_allows_delivery_and_sells_inventory(
    customer,
    active_store,
    seller_product,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.constants import InventoryMovementType
    from apps.inventory.models import Inventory, InventoryMovement
    from apps.orders.constants import OrderStatus
    from apps.orders.services.delivery_otp import DeliveryOTPService
    from apps.orders.services.order import OrderService

    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    cart = Cart.objects.create(
        customer=customer,
        store=active_store,
    )

    CartItem.objects.create(
        cart=cart,
        seller_product=seller_product,
        quantity=3,
        unit_price=Decimal("250.00"),
    )

    order = OrderService.create_order(
        customer=customer,
        cart=cart,
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )

    seller_owner = active_store.owner

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.ACCEPTED,
        actor=seller_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.PREPARING,
        actor=seller_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.READY,
        actor=seller_owner,
    )

    delivery_user = type(
        "DeliveryActor",
        (),
        {"role": "DELIVERY", "id": None},
    )()

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.OUT_FOR_DELIVERY,
        actor=delivery_user,
    )
    order.refresh_from_db()


    otp, code = DeliveryOTPService.create(
        order=order,
    )

    verified_otp = DeliveryOTPService.verify(
        order=order,
        otp_id=otp.id,
        code=code,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.DELIVERED,
        actor=delivery_user,
        delivery_otp_id=verified_otp.id,
    )

    order.refresh_from_db()
    inventory.refresh_from_db()

    assert order.status == OrderStatus.DELIVERED

    assert inventory.on_hand == 7
    assert inventory.reserved == 0
    assert inventory.available == 7

    assert InventoryMovement.objects.filter(
        inventory=inventory,
        movement_type=InventoryMovementType.SALE,
        quantity=3,
    ).count() == 1


@pytest.mark.django_db
def test_delivery_otp_from_another_order_cannot_deliver_order(
    customer,
    active_store,
    seller_product,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.models import Inventory
    from apps.orders.constants import OrderStatus
    from apps.orders.services.delivery_otp import DeliveryOTPService
    from apps.orders.services.order import OrderService

    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=20,
        reserved=0,
    )

    def create_order():
        cart = Cart.objects.create(
            customer=customer,
            store=active_store,
        )

        CartItem.objects.create(
            cart=cart,
            seller_product=seller_product,
            quantity=3,
            unit_price=Decimal("250.00"),
        )

        return OrderService.create_order(
            customer=customer,
            cart=cart,
            address_snapshot={
                "city": "Suez",
                "address": "Test Address",
            },
        )

    order_1 = create_order()
    order_2 = create_order()

    seller_owner = active_store.owner

    for order in (order_1, order_2):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.ACCEPTED,
            actor=seller_owner,
        )

        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.PREPARING,
            actor=seller_owner,
        )

        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.READY,
            actor=seller_owner,
        )

    delivery_user = type(
        "DeliveryActor",
        (),
        {"role": "DELIVERY", "id": None},
    )()

    OrderService.transition_status(
        order_id=order_1.id,
        new_status=OrderStatus.OUT_FOR_DELIVERY,
        actor=delivery_user,
    )

    OrderService.transition_status(
        order_id=order_2.id,
        new_status=OrderStatus.OUT_FOR_DELIVERY,
        actor=delivery_user,
    )

    order_1.refresh_from_db()
    order_2.refresh_from_db()

    otp_1, code_1 = DeliveryOTPService.create(
        order=order_1,
    )

    verified_otp_1 = DeliveryOTPService.verify(
        order=order_1,
        otp_id=otp_1.id,
        code=code_1,
    )

    with pytest.raises(
        ValueError,
        match="Delivery OTP not found.",
    ):
        OrderService.transition_status(
            order_id=order_2.id,
            new_status=OrderStatus.DELIVERED,
            actor=delivery_user,
            delivery_otp_id=verified_otp_1.id,
        )

    order_2.refresh_from_db()
    inventory.refresh_from_db()

    assert order_2.status == OrderStatus.OUT_FOR_DELIVERY

    assert inventory.on_hand == 20
    assert inventory.reserved == 6
    assert inventory.available == 14


@pytest.mark.django_db
def test_verified_delivery_otp_cannot_be_reused(
    customer,
    active_store,
    seller_product,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.models import Inventory
    from apps.orders.constants import OrderStatus
    from apps.orders.services.delivery_otp import DeliveryOTPService
    from apps.orders.services.order import OrderService

    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    cart = Cart.objects.create(
        customer=customer,
        store=active_store,
    )

    CartItem.objects.create(
        cart=cart,
        seller_product=seller_product,
        quantity=3,
        unit_price=Decimal("250.00"),
    )

    order = OrderService.create_order(
        customer=customer,
        cart=cart,
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )

    seller_owner = active_store.owner

    for status in (
        OrderStatus.ACCEPTED,
        OrderStatus.PREPARING,
        OrderStatus.READY,
    ):
        OrderService.transition_status(
            order_id=order.id,
            new_status=status,
            actor=seller_owner,
        )

    delivery_user = type(
        "DeliveryActor",
        (),
        {"role": "DELIVERY", "id": None},
    )()

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.OUT_FOR_DELIVERY,
        actor=delivery_user,
    )

    order.refresh_from_db()

    otp, code = DeliveryOTPService.create(order=order)

    verified_otp = DeliveryOTPService.verify(
        order=order,
        otp_id=otp.id,
        code=code,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.DELIVERED,
        actor=delivery_user,
        delivery_otp_id=verified_otp.id,
    )

    order.refresh_from_db()
    inventory.refresh_from_db()

    assert order.status == OrderStatus.DELIVERED
    assert inventory.on_hand == 7
    assert inventory.reserved == 0

    with pytest.raises(ValueError, match="Invalid order transition"):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.DELIVERED,
            actor=delivery_user,
            delivery_otp_id=verified_otp.id,
        )


@pytest.mark.django_db
def test_delivery_otp_delivery_rolls_back_when_inventory_sale_fails(
    customer,
    active_store,
    seller_product,
    monkeypatch,
):
    from decimal import Decimal

    from apps.cart.models import Cart, CartItem
    from apps.inventory.models import Inventory
    from apps.orders.constants import OrderStatus
    from apps.orders.services.delivery_otp import DeliveryOTPService
    from apps.orders.services.order import OrderService

    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    cart = Cart.objects.create(
        customer=customer,
        store=active_store,
    )

    CartItem.objects.create(
        cart=cart,
        seller_product=seller_product,
        quantity=3,
        unit_price=Decimal("250.00"),
    )

    order = OrderService.create_order(
        customer=customer,
        cart=cart,
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )

    seller_owner = active_store.owner

    for status in (
        OrderStatus.ACCEPTED,
        OrderStatus.PREPARING,
        OrderStatus.READY,
    ):
        OrderService.transition_status(
            order_id=order.id,
            new_status=status,
            actor=seller_owner,
        )

    delivery_user = type(
        "DeliveryActor",
        (),
        {"role": "DELIVERY", "id": None},
    )()

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.OUT_FOR_DELIVERY,
        actor=delivery_user,
    )

    order.refresh_from_db()

    otp, code = DeliveryOTPService.create(
        order=order,
    )

    verified_otp = DeliveryOTPService.verify(
        order=order,
        otp_id=otp.id,
        code=code,
    )

    def failing_sell(*args, **kwargs):
        raise RuntimeError("Simulated inventory sale failure")

    monkeypatch.setattr(
        "apps.orders.services.order.InventoryService.sell",
        failing_sell,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated inventory sale failure",
    ):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.DELIVERED,
            actor=delivery_user,
            delivery_otp_id=verified_otp.id,
        )

    order.refresh_from_db()
    inventory.refresh_from_db()

    assert order.status == OrderStatus.OUT_FOR_DELIVERY
    assert inventory.on_hand == 10
    assert inventory.reserved == 3
    assert inventory.available == 7