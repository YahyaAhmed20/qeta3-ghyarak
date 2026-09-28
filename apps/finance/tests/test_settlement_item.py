from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.finance.constants import CommissionStatus
from apps.finance.models import (
    Commission,
    Settlement,
    SettlementItem,
)


@pytest.fixture
def settlement(active_store):
    return Settlement.objects.create(
        store=active_store,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 8),
        gross_sales=Decimal("250.00"),
        commission_total=Decimal("17.50"),
        adjustments_total=Decimal("0.00"),
        net_amount=Decimal("232.50"),
    )


@pytest.fixture
def delivered_order(order):
    from apps.orders.constants import OrderStatus

    order.status = OrderStatus.DELIVERED
    order.save(update_fields=["status", "updated_at"])
    return order


@pytest.fixture
def commission(active_store, delivered_order):
    return Commission.objects.create(
        order=delivered_order,
        store=active_store,
        rate=Decimal("7.00"),
        base_amount=Decimal("250.00"),
        commission_amount=Decimal("17.50"),
        status=CommissionStatus.PENDING,
    )


@pytest.mark.django_db
def test_create_settlement_item(
    settlement,
    commission,
):
    item = SettlementItem.objects.create(
        settlement=settlement,
        commission=commission,
        gross_amount=Decimal("250.00"),
        commission_amount=Decimal("17.50"),
    )

    assert item.settlement_id == settlement.id
    assert item.commission_id == commission.id
    assert item.gross_amount == Decimal("250.00")
    assert item.commission_amount == Decimal("17.50")


@pytest.mark.django_db
def test_settlement_item_rejects_negative_gross_amount(
    settlement,
    commission,
):
    item = SettlementItem(
        settlement=settlement,
        commission=commission,
        gross_amount=Decimal("-1.00"),
        commission_amount=Decimal("17.50"),
    )

    with pytest.raises(ValidationError):
        item.full_clean()


@pytest.mark.django_db
def test_settlement_item_rejects_negative_commission_amount(
    settlement,
    commission,
):
    item = SettlementItem(
        settlement=settlement,
        commission=commission,
        gross_amount=Decimal("250.00"),
        commission_amount=Decimal("-1.00"),
    )

    with pytest.raises(ValidationError):
        item.full_clean()


@pytest.mark.django_db
def test_commission_cannot_be_added_twice(
    settlement,
    commission,
):
    SettlementItem.objects.create(
        settlement=settlement,
        commission=commission,
        gross_amount=Decimal("250.00"),
        commission_amount=Decimal("17.50"),
    )

    with pytest.raises(Exception):
        SettlementItem.objects.create(
            settlement=settlement,
            commission=commission,
            gross_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )


@pytest.mark.django_db
def test_non_settleable_commission_rejected(
    settlement,
    commission,
):
    commission.status = CommissionStatus.SETTLED
    commission.save(update_fields=["status", "updated_at"])

    item = SettlementItem(
        settlement=settlement,
        commission=commission,
        gross_amount=Decimal("250.00"),
        commission_amount=Decimal("17.50"),
    )

    with pytest.raises(ValidationError):
        item.full_clean()