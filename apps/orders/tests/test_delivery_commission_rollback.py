from decimal import Decimal
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.finance.models import Commission, CommissionRule
from apps.inventory.models import Inventory
from apps.orders.constants import DeliveryAssignmentStatus, OrderStatus
from apps.orders.models import DeliveryAssignment, OrderItem
from apps.orders.services.delivery_assignment import DeliveryAssignmentService
from apps.orders.services.delivery_otp import DeliveryOTPService


@pytest.mark.django_db
def test_delivery_rolls_back_if_commission_creation_fails(
    order,
    active_store,
    seller_product,
    delivery_user,
    admin_user,
    monkeypatch,
):
    order.status = OrderStatus.READY
    order.subtotal = Decimal("2300.00")
    order.seller_discount = Decimal("100.00")
    order.platform_discount = Decimal("50.00")
    order.delivery_fee = Decimal("80.00")
    order.total = Decimal("2230.00")
    order.save()

    OrderItem.objects.create(
        order=order,
        seller_product=seller_product,
        product_name_snapshot=seller_product.product.name,
        part_number_snapshot="TEST-PART-001",
        unit_price=Decimal("2300.00"),
        discount=Decimal("100.00"),
        quantity=1,
    )

    Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=1,
    )

    now = timezone.now()

    CommissionRule.objects.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=now - timedelta(minutes=1),
    )

    assignment = DeliveryAssignmentService.assign(
        order_id=order.id,
        delivery_user=delivery_user,
        actor=admin_user,
    )

    order.refresh_from_db()

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    assignment.refresh_from_db()

    otp, code = DeliveryOTPService.create(
        order=order,
    )

    inventory = Inventory.objects.get(
        seller_product=seller_product,
    )

    initial_on_hand = inventory.on_hand
    initial_reserved = inventory.reserved

    def fail_commission(*args, **kwargs):
        raise ValueError("Commission creation failed.")

    monkeypatch.setattr(
        "apps.finance.services.commission.CommissionService.create_for_order",
        fail_commission,
    )

    with pytest.raises(ValueError, match="Commission creation failed"):
        DeliveryAssignmentService.complete_delivery(
            assignment_id=assignment.id,
            actor=delivery_user,
            otp_id=otp.id,
            code=code,
        )

    order.refresh_from_db()
    assignment.refresh_from_db()
    otp.refresh_from_db()
    inventory.refresh_from_db()

    assert order.status == OrderStatus.OUT_FOR_DELIVERY

    assert assignment.status == DeliveryAssignmentStatus.ACCEPTED

    assert otp.status == "ACTIVE"
    assert otp.verified_at is None

    assert inventory.on_hand == initial_on_hand
    assert inventory.reserved == initial_reserved

    assert not Commission.objects.filter(
        order=order,
    ).exists()