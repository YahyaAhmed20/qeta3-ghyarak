import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.accounts.models import User
from apps.finance.models.settlement import Settlement


class SettlementAdjustmentType(models.TextChoices):
    SELLER_DEBIT = "SELLER_DEBIT", "Seller Debit"
    SELLER_CREDIT = "SELLER_CREDIT", "Seller Credit"
    REFUND = "REFUND", "Refund"
    DELIVERY_ADJUSTMENT = "DELIVERY_ADJUSTMENT", "Delivery Adjustment"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT", "Manual Adjustment"


class SettlementAdjustment(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    settlement = models.ForeignKey(
        Settlement,
        on_delete=models.PROTECT,
        related_name="adjustments",
    )

    adjustment_type = models.CharField(
        max_length=30,
        choices=SettlementAdjustmentType.choices,
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    reason = models.TextField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="settlement_adjustments",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "finance_settlement_adjustments"

        indexes = [
            models.Index(
                fields=["settlement"],
                name="fin_settle_adj_settle_idx",
            ),
            models.Index(
                fields=["adjustment_type"],
                name="fin_settle_adj_type_idx",
            ),
            models.Index(
                fields=["created_by"],
                name="fin_settle_adj_creator_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="fin_settle_adj_amount_positive",
            ),
        ]

    def clean(self):
        errors = {}

        if self.amount <= Decimal("0.00"):
            errors["amount"] = (
                "Adjustment amount must be greater than zero."
            )

        if not self.reason or not self.reason.strip():
            errors["reason"] = (
                "Adjustment reason is required."
            )

        if self.settlement_id and self.settlement.status in (
            "PAID",
            "CANCELLED",
        ):
            errors["settlement"] = (
                "Adjustments cannot be added to a paid or "
                "cancelled settlement."
            )

        if errors:
            raise ValidationError(errors)

    @property
    def is_debit(self):
        return self.adjustment_type in {
            SettlementAdjustmentType.SELLER_DEBIT,
            SettlementAdjustmentType.REFUND,
            SettlementAdjustmentType.DELIVERY_ADJUSTMENT,
        }

    @property
    def signed_amount(self):
        if self.is_debit:
            return -self.amount

        return self.amount

    def __str__(self):
        sign = "-" if self.is_debit else "+"

        return (
            f"{sign}{self.amount} | "
            f"{self.adjustment_type} | "
            f"{self.settlement_id}"
        )