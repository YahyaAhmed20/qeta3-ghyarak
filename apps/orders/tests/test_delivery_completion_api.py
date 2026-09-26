import pytest
from rest_framework.test import APIClient

from apps.inventory.models import Inventory
from apps.inventory.services.inventory import InventoryService
from apps.orders.constants import (
    DeliveryAssignmentStatus,
    OrderStatus,
)
from apps.orders.models import OrderItem
from apps.orders.services.delivery_assignment import DeliveryAssignmentService
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


@pytest.fixture
def delivery_scenario(
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

    otp, code = DeliveryOTPService.create(
        order=ready_order,
    )

    return {
        "inventory": inventory,
        "assignment": assignment,
        "order": ready_order,
        "otp": otp,
        "code": code,
    }


@pytest.mark.django_db
def test_assigned_delivery_can_complete_delivery(
    delivery_user,
    admin_user,
    ready_order,
    seller_product,
):
    client = APIClient()

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

    otp, code = DeliveryOTPService.create(
        order=ready_order,
    )

    client.force_authenticate(user=delivery_user)

    response = client.post(
        f"/api/v1/orders/delivery/assignments/"
        f"{assignment.id}/complete/",
        {
            "otp_id": str(otp.id),
            "code": code,
        },
        format="json",
    )

    assert response.status_code == 200

    ready_order.refresh_from_db()
    assignment.refresh_from_db()
    otp.refresh_from_db()
    inventory.refresh_from_db()

    assert ready_order.status == OrderStatus.DELIVERED
    assert assignment.status == DeliveryAssignmentStatus.DELIVERED
    assert otp.status == "VERIFIED"

    assert inventory.on_hand == 9
    assert inventory.reserved == 0


@pytest.mark.django_db
def test_another_delivery_cannot_complete_delivery(
    delivery_scenario,
    another_delivery_user,
):
    client = APIClient()
    client.force_authenticate(user=another_delivery_user)

    assignment = delivery_scenario["assignment"]
    otp = delivery_scenario["otp"]
    code = delivery_scenario["code"]

    response = client.post(
        f"/api/v1/orders/delivery/assignments/"
        f"{assignment.id}/complete/",
        {
            "otp_id": str(otp.id),
            "code": code,
        },
        format="json",
    )

    assert response.status_code == 403

    assignment.refresh_from_db()
    assert assignment.status == DeliveryAssignmentStatus.ACCEPTED


@pytest.mark.django_db
def test_invalid_otp_cannot_complete_delivery(
    delivery_scenario,
    delivery_user,
):
    client = APIClient()
    client.force_authenticate(user=delivery_user)

    assignment = delivery_scenario["assignment"]
    otp = delivery_scenario["otp"]

    response = client.post(
        f"/api/v1/orders/delivery/assignments/"
        f"{assignment.id}/complete/",
        {
            "otp_id": str(otp.id),
            "code": "000000",
        },
        format="json",
    )

    assert response.status_code == 400

    assignment.refresh_from_db()
    otp.refresh_from_db()

    assert assignment.status == DeliveryAssignmentStatus.ACCEPTED
    assert otp.status == "ACTIVE"
    assert otp.attempts == 1


@pytest.mark.django_db
def test_verified_delivery_otp_cannot_be_reused(
    delivery_scenario,
):
    scenario = delivery_scenario

    assignment = scenario["assignment"]
    otp = scenario["otp"]
    code = scenario["code"]

    client = APIClient()

    client.force_authenticate(
        user=assignment.delivery_user,
    )

    url = (
        f"/api/v1/orders/delivery/assignments/"
        f"{assignment.id}/complete/"
    )

    response = client.post(
        url,
        {
            "otp_id": str(otp.id),
            "code": code,
        },
        format="json",
    )

    assert response.status_code == 200

    otp.refresh_from_db()
    assert otp.status == "VERIFIED"

    response = client.post(
        url,
        {
            "otp_id": str(otp.id),
            "code": code,
        },
        format="json",
    )

    assert response.status_code == 400

    otp.refresh_from_db()
    assert otp.status == "VERIFIED"


@pytest.mark.django_db
def test_delivery_otp_remains_active_after_delivery_transaction_rollback(
    delivery_scenario,
    monkeypatch,
):
    scenario = delivery_scenario

    assignment = scenario["assignment"]
    otp = scenario["otp"]
    code = scenario["code"]

    def fail_sell(*args, **kwargs):
        raise ValueError("Simulated inventory failure.")

    monkeypatch.setattr(
        InventoryService,
        "sell",
        fail_sell,
    )

    client = APIClient()

    client.force_authenticate(
        user=assignment.delivery_user,
    )

    url = (
        f"/api/v1/orders/delivery/assignments/"
        f"{assignment.id}/complete/"
    )

    response = client.post(
        url,
        {
            "otp_id": str(otp.id),
            "code": code,
        },
        format="json",
    )

    assert response.status_code == 400

    otp.refresh_from_db()
    assignment.refresh_from_db()
    scenario["order"].refresh_from_db()
    scenario["inventory"].refresh_from_db()

    assert otp.status == "ACTIVE"
    assert otp.verified_at is None

    assert assignment.status == DeliveryAssignmentStatus.ACCEPTED
    assert scenario["order"].status == OrderStatus.OUT_FOR_DELIVERY

    assert scenario["inventory"].on_hand == 10
    assert scenario["inventory"].reserved == 1