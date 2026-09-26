import pytest

from apps.inventory.models import Inventory
from apps.inventory.services.inventory import InventoryService
from apps.orders.constants import (
    DeliveryAssignmentStatus,
    OrderStatus,
)
from apps.orders.models import DeliveryAssignment, OrderItem
from apps.orders.services.delivery_assignment import (
    DeliveryAssignmentService,
)
from apps.orders.services.delivery_otp import DeliveryOTPService
from apps.orders.services.order import OrderService


@pytest.fixture
def ready_order(order, seller_owner):
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

    order.refresh_from_db()
    return order


def test_delivery_user_can_be_assigned_to_ready_order(
    ready_order,
    delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    assignment.refresh_from_db()
    ready_order.refresh_from_db()

    assert assignment.delivery_user_id == delivery_user.id
    assert assignment.status == DeliveryAssignmentStatus.ASSIGNED
    assert assignment.order_id == ready_order.id
    assert ready_order.status == OrderStatus.OUT_FOR_DELIVERY


def test_non_delivery_user_cannot_be_assigned(
    ready_order,
    customer,
    admin_user,
):
    with pytest.raises(ValueError, match="DELIVERY role"):
        DeliveryAssignmentService.assign(
            order_id=ready_order.id,
            delivery_user=customer,
            actor=admin_user,
        )


def test_only_ready_order_can_be_assigned(
    order,
    delivery_user,
    admin_user,
):
    with pytest.raises(
        ValueError,
        match="Only READY orders can be assigned",
    ):
        DeliveryAssignmentService.assign(
            order_id=order.id,
            delivery_user=delivery_user,
            actor=admin_user,
        )


def test_order_cannot_have_two_active_delivery_assignments(
    ready_order,
    delivery_user,
    another_delivery_user,
    admin_user,
):
    DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    with pytest.raises(
        ValueError,
        match="already has an active delivery assignment",
    ):
        DeliveryAssignmentService.assign(
            order_id=ready_order.id,
            delivery_user=another_delivery_user,
            actor=admin_user,
        )


def test_assigned_delivery_user_can_accept(
    ready_order,
    delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    assignment = DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    assignment.refresh_from_db()

    assert assignment.status == DeliveryAssignmentStatus.ACCEPTED
    assert assignment.accepted_at is not None


def test_another_delivery_user_cannot_accept_assignment(
    ready_order,
    delivery_user,
    another_delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    with pytest.raises(
        PermissionError,
        match="assigned delivery user",
    ):
        DeliveryAssignmentService.accept(
            assignment_id=assignment.id,
            actor=another_delivery_user,
        )


def test_non_delivery_user_cannot_accept_assignment(
    ready_order,
    delivery_user,
    customer,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    with pytest.raises(
        PermissionError,
        match="DELIVERY users",
    ):
        DeliveryAssignmentService.accept(
            assignment_id=assignment.id,
            actor=customer,
        )


def test_assignment_cannot_be_accepted_twice(
    ready_order,
    delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    with pytest.raises(
        ValueError,
        match="Only ASSIGNED deliveries can be accepted",
    ):
        DeliveryAssignmentService.accept(
            assignment_id=assignment.id,
            actor=delivery_user,
        )


def test_assigned_delivery_user_can_cancel(
    ready_order,
    delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    assignment = DeliveryAssignmentService.cancel(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    assignment.refresh_from_db()

    assert assignment.status == DeliveryAssignmentStatus.CANCELLED


def test_admin_can_cancel_assignment(
    ready_order,
    delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    assignment = DeliveryAssignmentService.cancel(
        assignment_id=assignment.id,
        actor=admin_user,
    )

    assignment.refresh_from_db()

    assert assignment.status == DeliveryAssignmentStatus.CANCELLED


def test_unrelated_user_cannot_cancel_assignment(
    ready_order,
    delivery_user,
    another_delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    with pytest.raises(
        PermissionError,
        match="permission to cancel",
    ):
        DeliveryAssignmentService.cancel(
            assignment_id=assignment.id,
            actor=another_delivery_user,
        )


def test_cancelled_assignment_cannot_be_cancelled_again(
    ready_order,
    delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.cancel(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    with pytest.raises(
        ValueError,
        match="Only active delivery assignments",
    ):
        DeliveryAssignmentService.cancel(
            assignment_id=assignment.id,
            actor=delivery_user,
        )


def test_cancelled_assignment_cannot_be_accepted(
    ready_order,
    delivery_user,
    admin_user,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.cancel(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    with pytest.raises(
        ValueError,
        match="Only ASSIGNED deliveries can be accepted",
    ):
        DeliveryAssignmentService.accept(
            assignment_id=assignment.id,
            actor=delivery_user,
        )


def test_accept_moves_order_to_out_for_delivery(
    delivery_user,
    admin_user,
    ready_order,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    ready_order.refresh_from_db()

    assert (
        ready_order.status
        == OrderStatus.OUT_FOR_DELIVERY
    )


def test_delivery_can_complete_order_with_verified_otp(
    delivery_user,
    admin_user,
    ready_order,
):
    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    ready_order.refresh_from_db()

    assert ready_order.status == OrderStatus.OUT_FOR_DELIVERY

    otp, code = DeliveryOTPService.create(
        order=ready_order,
    )

    verified_otp = DeliveryOTPService.verify(
        order=ready_order,
        otp_id=otp.id,
        code=code,
    )

    OrderService.transition_status(
        order_id=ready_order.id,
        new_status=OrderStatus.DELIVERED,
        actor=delivery_user,
        delivery_otp_id=verified_otp.id,
    )

    ready_order.refresh_from_db()

    assert ready_order.status == OrderStatus.DELIVERED


def test_delivery_sells_reserved_inventory(
    delivery_user,
    admin_user,
    ready_order,
    seller_product,
):
    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    OrderItem.objects.create(
        order=ready_order,
        seller_product=seller_product,
        product_name_snapshot=seller_product.product.name,
        part_number_snapshot="BOSCH-TEST-001",
        unit_price="250.00",
        discount="0.00",
        quantity=1,
    )

    InventoryService.reserve(
        inventory_id=inventory.id,
        quantity=1,
    )

    inventory.refresh_from_db()

    reserved_before = inventory.reserved
    on_hand_before = inventory.on_hand

    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    ready_order.refresh_from_db()

    assert ready_order.status == OrderStatus.OUT_FOR_DELIVERY

    otp, code = DeliveryOTPService.create(
        order=ready_order,
    )

    verified_otp = DeliveryOTPService.verify(
        order=ready_order,
        otp_id=otp.id,
        code=code,
    )

    OrderService.transition_status(
        order_id=ready_order.id,
        new_status=OrderStatus.DELIVERED,
        actor=delivery_user,
        delivery_otp_id=verified_otp.id,
    )

    inventory.refresh_from_db()

    assert inventory.reserved == reserved_before - 1
    assert inventory.on_hand == on_hand_before - 1


@pytest.mark.django_db
def test_assigned_delivery_can_complete_delivery_atomically(
    delivery_user,
    admin_user,
    ready_order,
    seller_product,
):
    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    OrderItem.objects.create(
        order=ready_order,
        seller_product=seller_product,
        product_name_snapshot=seller_product.product.name,
        part_number_snapshot="BOSCH-TEST-001",
        unit_price="250.00",
        discount="0.00",
        quantity=1,
    )

    InventoryService.reserve(
        inventory_id=inventory.id,
        quantity=1,
    )

    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    ready_order.refresh_from_db()

    assert ready_order.status == OrderStatus.OUT_FOR_DELIVERY

    otp, code = DeliveryOTPService.create(
        order=ready_order,
    )

    completed = DeliveryAssignmentService.complete_delivery(
        assignment_id=assignment.id,
        otp_id=otp.id,
        code=code,
        actor=delivery_user,
    )

    ready_order.refresh_from_db()
    assignment.refresh_from_db()
    otp.refresh_from_db()
    inventory.refresh_from_db()

    assert completed.id == assignment.id

    assert ready_order.status == OrderStatus.DELIVERED
    assert assignment.status == DeliveryAssignmentStatus.DELIVERED
    assert assignment.completed_at is not None

    assert otp.status == "VERIFIED"
    assert otp.verified_at is not None

    assert inventory.on_hand == 9
    assert inventory.reserved == 0


@pytest.mark.django_db
def test_complete_delivery_rolls_back_when_inventory_sale_fails(
    delivery_user,
    admin_user,
    ready_order,
    seller_product,
    monkeypatch,
):
    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=1,
    )

    OrderItem.objects.create(
        order=ready_order,
        seller_product=seller_product,
        product_name_snapshot=seller_product.product.name,
        part_number_snapshot="BOSCH-TEST-001",
        unit_price="250.00",
        discount="0.00",
        quantity=1,
    )

    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    ready_order.refresh_from_db()

    otp, code = DeliveryOTPService.create(
        order=ready_order,
    )

    def fail_sale(*args, **kwargs):
        raise ValueError("Simulated inventory sale failure.")

    monkeypatch.setattr(
        InventoryService,
        "sell",
        fail_sale,
    )

    with pytest.raises(
        ValueError,
        match="Simulated inventory sale failure.",
    ):
        DeliveryAssignmentService.complete_delivery(
            assignment_id=assignment.id,
            otp_id=otp.id,
            code=code,
            actor=delivery_user,
        )

    ready_order.refresh_from_db()
    assignment.refresh_from_db()
    otp.refresh_from_db()
    inventory.refresh_from_db()

    assert ready_order.status == OrderStatus.OUT_FOR_DELIVERY

    assert assignment.status == DeliveryAssignmentStatus.ACCEPTED
    assert assignment.completed_at is None

    assert otp.status == "ACTIVE"
    assert otp.verified_at is None

    assert inventory.on_hand == 10
    assert inventory.reserved == 1


@pytest.mark.django_db
def test_complete_delivery_invalid_otp_preserves_failed_attempt(
    delivery_user,
    admin_user,
    ready_order,
    seller_product,
):
    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    OrderItem.objects.create(
        order=ready_order,
        seller_product=seller_product,
        product_name_snapshot=seller_product.product.name,
        part_number_snapshot="BOSCH-TEST-001",
        unit_price="250.00",
        discount="0.00",
        quantity=1,
    )

    InventoryService.reserve(
        inventory_id=inventory.id,
        quantity=1,
    )

    assignment = DeliveryAssignmentService.assign(
        order_id=ready_order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    ready_order.refresh_from_db()

    otp, _ = DeliveryOTPService.create(
        order=ready_order,
    )

    with pytest.raises(
        ValueError,
        match="Invalid delivery OTP.",
    ):
        DeliveryAssignmentService.complete_delivery(
            assignment_id=assignment.id,
            otp_id=otp.id,
            code="000000",
            actor=delivery_user,
        )

    otp.refresh_from_db()
    assignment.refresh_from_db()
    ready_order.refresh_from_db()
    inventory.refresh_from_db()

    assert otp.attempts == 1
    assert otp.status == "ACTIVE"

    assert assignment.status == DeliveryAssignmentStatus.ACCEPTED
    assert ready_order.status == OrderStatus.OUT_FOR_DELIVERY

    assert inventory.on_hand == 10
    assert inventory.reserved == 1