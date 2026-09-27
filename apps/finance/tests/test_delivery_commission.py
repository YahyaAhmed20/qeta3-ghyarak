from decimal import Decimal

import pytest

from apps.finance.models import Commission
from apps.orders.constants import OrderStatus
from apps.orders.services.delivery_assignment import (
    DeliveryAssignmentService,
)
from apps.orders.services.delivery_otp import DeliveryOTPService
from apps.orders.services.order import OrderService


@pytest.mark.django_db
def test_successful_delivery_creates_commission(
    order,
    finance_owner,
    delivery_user,
    finance_admin,
    commission_rule,
):
    commission_rule.rate = Decimal("7.00")
    commission_rule.save(
        update_fields=["rate", "updated_at"],
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.ACCEPTED,
        actor=finance_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.PREPARING,
        actor=finance_owner,
    )

    OrderService.transition_status(
        order_id=order.id,
        new_status=OrderStatus.READY,
        actor=finance_owner,
    )

    order.refresh_from_db()

    assignment = DeliveryAssignmentService.assign(
        order_id=order.id,
        delivery_user=delivery_user,
        actor=finance_admin,
    )

    DeliveryAssignmentService.accept(
        assignment_id=assignment.id,
        actor=delivery_user,
    )

    order.refresh_from_db()

    assert order.status == OrderStatus.OUT_FOR_DELIVERY

    otp, code = DeliveryOTPService.create(
        order=order,
    )

    DeliveryAssignmentService.complete_delivery(
        assignment_id=assignment.id,
        actor=delivery_user,
        otp_id=otp.id,
        code=code,
    )

    order.refresh_from_db()

    assert order.status == OrderStatus.DELIVERED

    commission = Commission.objects.get(
        order=order,
    )

    assert commission.store_id == order.store_id
    assert commission.rate == Decimal("7.00")
    assert commission.base_amount == (
        order.subtotal - order.seller_discount
    )
    assert commission.commission_amount == Decimal("17.50")