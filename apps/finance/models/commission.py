import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.finance.constants import CommissionStatus
from apps.orders.models import Order
from apps.stores.models import Store


class Commission(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="commission",
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="commissions",
    )

    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    base_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=CommissionStatus.choices,
        default=CommissionStatus.PENDING,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["store", "status"],
            ),
            models.Index(
                fields=["order", "status"],
            ),
        ]

    def clean(self):
        if self.rate < 0 or self.rate > 100:
            raise ValidationError(
                {"rate": "Commission rate must be between 0 and 100."}
            )

        if self.base_amount < 0:
            raise ValidationError(
                {"base_amount": "Base amount cannot be negative."}
            )

        if self.commission_amount < 0:
            raise ValidationError(
                {"commission_amount": "Commission amount cannot be negative."}
            )

    def __str__(self):
        return f"{self.order.order_number} - {self.commission_amount}"