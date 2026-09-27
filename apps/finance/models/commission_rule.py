import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.stores.models import Store


class CommissionRule(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="commission_rules",
    )

    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    effective_from = models.DateTimeField()

    effective_to = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-effective_from"]
        indexes = [
            models.Index(
                fields=[
                    "store",
                    "is_active",
                    "effective_from",
                ]
            ),
        ]

    def clean(self):
        if self.rate < 0:
            raise ValidationError(
                {"rate": "Commission rate cannot be negative."}
            )

        if self.rate > 100:
            raise ValidationError(
                {"rate": "Commission rate cannot exceed 100%."}
            )

        if (
            self.effective_to is not None
            and self.effective_to <= self.effective_from
        ):
            raise ValidationError(
                {
                    "effective_to": (
                        "effective_to must be later than "
                        "effective_from."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.store.name} - "
            f"{self.rate}% from "
            f"{self.effective_from}"
        )