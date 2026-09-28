import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.finance.models.commission import Commission
from apps.finance.models.settlement import Settlement


class SettlementItem(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    settlement = models.ForeignKey(
        Settlement,
        on_delete=models.PROTECT,
        related_name="items",
    )

    commission = models.OneToOneField(
        Commission,
        on_delete=models.PROTECT,
        related_name="settlement_item",
    )

    gross_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    commission_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "finance_settlement_items"

        indexes = [
            models.Index(
                fields=["settlement"],
                name="fin_settle_item_settle_idx",
            ),
            models.Index(
                fields=["commission"],
                name="fin_settle_item_comm_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(gross_amount__gte=0),
                name="fin_settle_item_gross_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(commission_amount__gte=0),
                name="fin_settle_item_comm_nonnegative",
            ),
        ]

    def clean(self):
        errors = {}

        if self.gross_amount < 0:
            errors["gross_amount"] = (
                "Gross amount cannot be negative."
            )

        if self.commission_amount < 0:
            errors["commission_amount"] = (
                "Commission amount cannot be negative."
            )

        if self.commission_id and self.commission:
            if self.commission.status not in (
                "PENDING",
                "READY",
            ):
                errors["commission"] = (
                    "Only pending or ready commissions can be "
                    "included in a settlement."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.settlement_id} | "
            f"{self.commission_id}"
        )