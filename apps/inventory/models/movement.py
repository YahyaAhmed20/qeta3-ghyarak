import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.inventory.constants import InventoryMovementType


class InventoryMovement(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    inventory = models.ForeignKey(
        "inventory.Inventory",
        on_delete=models.PROTECT,
        related_name="movements",
    )

    movement_type = models.CharField(
        max_length=20,
        choices=InventoryMovementType.choices,
        db_index=True,
    )

    quantity = models.PositiveIntegerField()

    reference_type = models.CharField(
        max_length=50,
        blank=True,
    )

    reference_id = models.CharField(
        max_length=100,
        blank=True,
    )

    note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inventory_movements",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError(
                {"quantity": "Movement quantity must be greater than zero."}
            )

    def __str__(self):
        return (
            f"{self.movement_type} - "
            f"{self.quantity} - "
            f"{self.inventory_id}"
        )