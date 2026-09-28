from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.finance.models import Settlement, SettlementStatus


@pytest.mark.django_db
def test_create_pending_settlement(active_store):
    settlement = Settlement.objects.create(
        store=active_store,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 8),
        gross_sales=Decimal("5000.00"),
        commission_total=Decimal("350.00"),
        adjustments_total=Decimal("0.00"),
        net_amount=Decimal("4650.00"),
    )

    assert settlement.status == SettlementStatus.PENDING
    assert settlement.store_id == active_store.id
    assert settlement.gross_sales == Decimal("5000.00")
    assert settlement.commission_total == Decimal("350.00")
    assert settlement.net_amount == Decimal("4650.00")


@pytest.mark.django_db
def test_settlement_rejects_invalid_period(active_store):
    settlement = Settlement(
        store=active_store,
        period_start=date(2026, 9, 8),
        period_end=date(2026, 9, 1),
    )

    with pytest.raises(ValidationError):
        settlement.full_clean()


@pytest.mark.django_db
def test_settlement_rejects_negative_gross_sales(active_store):
    settlement = Settlement(
        store=active_store,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 8),
        gross_sales=Decimal("-1.00"),
    )

    with pytest.raises(ValidationError):
        settlement.full_clean()


@pytest.mark.django_db
def test_settlement_rejects_negative_commission(active_store):
    settlement = Settlement(
        store=active_store,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 8),
        commission_total=Decimal("-1.00"),
    )

    with pytest.raises(ValidationError):
        settlement.full_clean()


@pytest.mark.django_db
def test_settlement_rejects_negative_net_amount(active_store):
    settlement = Settlement(
        store=active_store,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 8),
        net_amount=Decimal("-1.00"),
    )

    with pytest.raises(ValidationError):
        settlement.full_clean()


@pytest.mark.django_db
def test_paid_settlement_requires_payment_reference(active_store):
    settlement = Settlement(
        store=active_store,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 8),
        status=SettlementStatus.PAID,
    )

    with pytest.raises(ValidationError):
        settlement.full_clean()


@pytest.mark.django_db
def test_mark_paid_requires_processing_status(active_store):
    settlement = Settlement.objects.create(
        store=active_store,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 8),
    )

    with pytest.raises(ValidationError):
        settlement.mark_paid("PAY-001")


@pytest.mark.django_db
def test_mark_paid_sets_payment_data(active_store):
    settlement = Settlement.objects.create(
        store=active_store,
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 8),
        status=SettlementStatus.PROCESSING,
    )

    settlement.mark_paid("PAY-001")

    assert settlement.status == SettlementStatus.PAID
    assert settlement.payment_reference == "PAY-001"
    assert settlement.paid_at is not None