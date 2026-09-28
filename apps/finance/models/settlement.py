import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.stores.models import Store


class SettlementStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    READY = "READY", "Ready"
    PROCESSING = "PROCESSING", "Processing"
    PAID = "PAID", "Paid"
    DISPUTED = "DISPUTED", "Disputed"
    CANCELLED = "CANCELLED", "Cancelled"


class Settlement(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="settlements",
    )

    period_start = models.DateField()
    period_end = models.DateField()

    gross_sales = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    commission_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    adjustments_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    net_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    status = models.CharField(
        max_length=20,
        choices=SettlementStatus.choices,
        default=SettlementStatus.PENDING,
    )

    payment_reference = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    paid_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "finance_settlements"

        indexes = [
            models.Index(
                fields=["store", "status"],
                name="fin_settle_store_status_idx",
            ),
            models.Index(
                fields=["period_start", "period_end"],
                name="fin_settle_period_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(period_start__lt=models.F("period_end")),
                name="fin_settle_valid_period",
            ),
            models.CheckConstraint(
                condition=Q(gross_sales__gte=0),
                name="fin_settle_gross_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(commission_total__gte=0),
                name="fin_settle_commission_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(net_amount__gte=0),
                name="fin_settle_net_nonnegative",
            ),
        ]

    def clean(self):
        errors = {}

        if self.period_start and self.period_end:
            if self.period_start >= self.period_end:
                errors["period_end"] = (
                    "Settlement period end must be after period start."
                )

        if self.gross_sales < 0:
            errors["gross_sales"] = (
                "Gross sales cannot be negative."
            )

        if self.commission_total < 0:
            errors["commission_total"] = (
                "Commission total cannot be negative."
            )

        if self.net_amount < 0:
            errors["net_amount"] = (
                "Net amount cannot be negative."
            )

        if self.status == SettlementStatus.PAID:
            if not self.payment_reference:
                errors["payment_reference"] = (
                    "Payment reference is required for paid settlements."
                )

            if not self.paid_at:
                errors["paid_at"] = (
                    "Paid timestamp is required for paid settlements."
                )

        if errors:
            raise ValidationError(errors)

    def mark_paid(self, payment_reference: str):
        if self.status != SettlementStatus.PROCESSING:
            raise ValidationError(
                "Only processing settlements can be marked as paid."
            )

        if not payment_reference:
            raise ValidationError(
                "Payment reference is required."
            )

        self.status = SettlementStatus.PAID
        self.payment_reference = payment_reference
        self.paid_at = timezone.now()

    def __str__(self):
        return (
            f"{self.store.name} | "
            f"{self.period_start} → {self.period_end}"
        )