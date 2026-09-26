import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.orders.constants import DeliveryAssignmentStatus
from apps.orders.models.order import Order


class DeliveryAssignment(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="delivery_assignments",
    )

    delivery_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="delivery_assignments",
    )

    status = models.CharField(
        max_length=20,
        choices=DeliveryAssignmentStatus.choices,
        default=DeliveryAssignmentStatus.ASSIGNED,
        db_index=True,
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True,
    )

    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["order", "status"],
            ),
            models.Index(
                fields=["delivery_user", "status"],
            ),
        ]

    def clean(self):
        if self.delivery_user.role != "DELIVERY":
            raise ValidationError(
                {
                    "delivery_user": (
                        "Delivery assignment user must have DELIVERY role."
                    )
                }
            )

        if self.order.status not in {
            "READY",
            "OUT_FOR_DELIVERY",
            "FAILED_DELIVERY",
        }:
            raise ValidationError(
                {
                    "order": (
                        "Order is not in a valid status for delivery assignment."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.order.order_number} → "
            f"{self.delivery_user.phone}"
        )