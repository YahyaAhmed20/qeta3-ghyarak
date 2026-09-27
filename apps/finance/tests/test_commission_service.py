from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.finance.models import Commission, CommissionRule
from apps.finance.services.commission import CommissionService
from apps.orders.constants import OrderStatus


@pytest.fixture
def delivered_order(db, active_store, finance_owner):
    from apps.accounts.models import User
    from apps.orders.models import Order

    customer = User.objects.create_user(
        phone="+201001234590",
        role="CUSTOMER",
        is_active=True,
    )

    return Order.objects.create(
        customer=customer,
        store=active_store,
        status=OrderStatus.DELIVERED,
        subtotal=Decimal("2300.00"),
        seller_discount=Decimal("100.00"),
        platform_discount=Decimal("50.00"),
        delivery_fee=Decimal("80.00"),
        total=Decimal("2230.00"),
        address_snapshot={
            "address": "Test Address",
            "city": "Suez",
        },
    )


@pytest.fixture
def commission_rule(active_store):
    return CommissionRule.objects.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=timezone.now() - timedelta(days=1),
    )


@pytest.mark.django_db
def test_create_commission(
    delivered_order,
    commission_rule,
):
    commission = CommissionService.create_for_order(
        order=delivered_order,
    )

    assert commission.pk is not None
    assert commission.order == delivered_order
    assert commission.store == delivered_order.store
    assert commission.rate == Decimal("7.00")
    assert commission.base_amount == Decimal("2200.00")
    assert commission.commission_amount == Decimal("154.00")


@pytest.mark.django_db
def test_commission_base_excludes_delivery_fee(
    delivered_order,
    commission_rule,
):
    commission = CommissionService.create_for_order(
        order=delivered_order,
    )

    assert commission.base_amount == Decimal("2200.00")
    assert commission.base_amount != (
        delivered_order.total - delivered_order.delivery_fee
    )


@pytest.mark.django_db
def test_platform_discount_does_not_reduce_commission_base(
    delivered_order,
    commission_rule,
):
    commission = CommissionService.create_for_order(
        order=delivered_order,
    )

    # Seller discount reduces the commission base.
    # Platform discount is funded by the platform.
    assert commission.base_amount == Decimal("2200.00")


@pytest.mark.django_db
def test_rate_is_snapshotted(
    delivered_order,
    commission_rule,
):
    commission = CommissionService.create_for_order(
        order=delivered_order,
    )

    commission_rule.rate = Decimal("8.00")
    commission_rule.save(update_fields=["rate", "updated_at"])

    commission.refresh_from_db()

    assert commission.rate == Decimal("7.00")
    assert commission.commission_amount == Decimal("154.00")


@pytest.mark.django_db
def test_cannot_create_duplicate_commission(
    delivered_order,
    commission_rule,
):
    first = CommissionService.create_for_order(
        order=delivered_order,
    )

    with pytest.raises(ValueError, match="already exists"):
        CommissionService.create_for_order(
            order=delivered_order,
        )

    assert Commission.objects.filter(
        order=delivered_order,
    ).count() == 1

    assert first.pk is not None


@pytest.mark.django_db
def test_order_must_be_delivered(
    delivered_order,
    commission_rule,
):
    delivered_order.status = OrderStatus.READY
    delivered_order.save(update_fields=["status", "updated_at"])

    with pytest.raises(ValueError, match="DELIVERED"):
        CommissionService.create_for_order(
            order=delivered_order,
        )

    assert Commission.objects.count() == 0


@pytest.mark.django_db
def test_missing_commission_rule_is_rejected(
    delivered_order,
):
    with pytest.raises(ValueError, match="commission rule"):
        CommissionService.create_for_order(
            order=delivered_order,
        )

    assert Commission.objects.count() == 0


@pytest.mark.django_db
def test_latest_effective_rule_is_used(
    delivered_order,
    active_store,
):
    now = timezone.now()

    CommissionRule.objects.create(
        store=active_store,
        rate=Decimal("5.00"),
        effective_from=now - timedelta(days=30),
        effective_to=now - timedelta(days=10),
    )

    latest_rule = CommissionRule.objects.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=now - timedelta(days=10),
    )

    commission = CommissionService.create_for_order(
        order=delivered_order,
    )

    assert commission.rate == latest_rule.rate
    assert commission.commission_amount == Decimal("154.00")