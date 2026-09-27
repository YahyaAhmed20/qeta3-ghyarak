from decimal import Decimal
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.finance.models import Commission, CommissionRule
from apps.orders.constants import OrderStatus
from apps.orders.models import DeliveryAssignment
from apps.orders.services.delivery_assignment import DeliveryAssignmentService
from apps.orders.services.delivery_otp import DeliveryOTPService


@pytest.mark.django_db
def test_successful_delivery_creates_commission(
    order,
    active_store,
    delivery_user,
    admin_user,
):
    order.status = OrderStatus.READY
    order.subtotal = Decimal("2300.00")
    order.seller_discount = Decimal("100.00")
    order.platform_discount = Decimal("50.00")
    order.delivery_fee = Decimal("80.00")
    order.total = Decimal("2230.00")
    order.save()

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

    result = DeliveryAssignmentService.complete_delivery(
        assignment_id=assignment.id,
        actor=delivery_user,
        otp_id=otp.id,
        code=code,
    )

    assert result.status == "DELIVERED"

    order.refresh_from_db()

    assert order.status == OrderStatus.DELIVERED

    commission = Commission.objects.get(
        order=order,
    )

    assert commission.store_id == order.store_id
    assert commission.rate == Decimal("7.00")
    assert commission.base_amount == Decimal("2200.00")
    assert commission.commission_amount == Decimal("154.00")