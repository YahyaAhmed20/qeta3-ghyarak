from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.finance.models import (
    Settlement,
    SettlementAdjustment,
    SettlementAdjustmentType,
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
def adjustment_user(db):
    return User.objects.create_user(
        phone="+201001234573",
        role="ADMIN",
        is_active=True,
    )


@pytest.mark.django_db
def test_create_seller_debit(
    settlement,
    adjustment_user,
):
    adjustment = SettlementAdjustment.objects.create(
        settlement=settlement,
        adjustment_type=SettlementAdjustmentType.SELLER_DEBIT,
        amount=Decimal("100.00"),
        reason="Customer complaint adjustment",
        created_by=adjustment_user,
    )

    assert adjustment.amount == Decimal("100.00")
    assert adjustment.is_debit is True
    assert adjustment.signed_amount == Decimal("-100.00")


@pytest.mark.django_db
def test_create_seller_credit(
    settlement,
    adjustment_user,
):
    adjustment = SettlementAdjustment.objects.create(
        settlement=settlement,
        adjustment_type=SettlementAdjustmentType.SELLER_CREDIT,
        amount=Decimal("50.00"),
        reason="Manual seller credit",
        created_by=adjustment_user,
    )

    assert adjustment.is_debit is False
    assert adjustment.signed_amount == Decimal("50.00")


@pytest.mark.django_db
def test_refund_is_debit(
    settlement,
    adjustment_user,
):
    adjustment = SettlementAdjustment(
        settlement=settlement,
        adjustment_type=SettlementAdjustmentType.REFUND,
        amount=Decimal("75.00"),
        reason="Customer refund",
        created_by=adjustment_user,
    )

    assert adjustment.is_debit is True
    assert adjustment.signed_amount == Decimal("-75.00")


@pytest.mark.django_db
def test_adjustment_rejects_zero_amount(
    settlement,
    adjustment_user,
):
    adjustment = SettlementAdjustment(
        settlement=settlement,
        adjustment_type=SettlementAdjustmentType.SELLER_DEBIT,
        amount=Decimal("0.00"),
        reason="Invalid adjustment",
        created_by=adjustment_user,
    )

    with pytest.raises(ValidationError):
        adjustment.full_clean()


@pytest.mark.django_db
def test_adjustment_rejects_negative_amount(
    settlement,
    adjustment_user,
):
    adjustment = SettlementAdjustment(
        settlement=settlement,
        adjustment_type=SettlementAdjustmentType.SELLER_DEBIT,
        amount=Decimal("-10.00"),
        reason="Invalid adjustment",
        created_by=adjustment_user,
    )

    with pytest.raises(ValidationError):
        adjustment.full_clean()


@pytest.mark.django_db
def test_adjustment_requires_reason(
    settlement,
    adjustment_user,
):
    adjustment = SettlementAdjustment(
        settlement=settlement,
        adjustment_type=SettlementAdjustmentType.SELLER_DEBIT,
        amount=Decimal("10.00"),
        reason="",
        created_by=adjustment_user,
    )

    with pytest.raises(ValidationError):
        adjustment.full_clean()


@pytest.mark.django_db
def test_adjustment_rejected_for_paid_settlement(
    settlement,
    adjustment_user,
):
    settlement.status = "PAID"
    settlement.payment_reference = "PAY-001"
    settlement.paid_at = settlement.created_at
    settlement.save(
        update_fields=[
            "status",
            "payment_reference",
            "paid_at",
            "updated_at",
        ],
    )

    adjustment = SettlementAdjustment(
        settlement=settlement,
        adjustment_type=SettlementAdjustmentType.SELLER_DEBIT,
        amount=Decimal("10.00"),
        reason="Late adjustment",
        created_by=adjustment_user,
    )

    with pytest.raises(ValidationError):
        adjustment.full_clean()


@pytest.mark.django_db
def test_adjustment_rejected_for_cancelled_settlement(
    settlement,
    adjustment_user,
):
    settlement.status = "CANCELLED"
    settlement.save(
        update_fields=["status", "updated_at"],
    )

    adjustment = SettlementAdjustment(
        settlement=settlement,
        adjustment_type=SettlementAdjustmentType.SELLER_DEBIT,
        amount=Decimal("10.00"),
        reason="Cancelled settlement adjustment",
        created_by=adjustment_user,
    )

    with pytest.raises(ValidationError):
        adjustment.full_clean()