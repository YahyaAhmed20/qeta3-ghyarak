import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Inventory(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    seller_product = models.OneToOneField(
        "stores.SellerProduct",
        on_delete=models.PROTECT,
        related_name="inventory",
    )

    on_hand = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def available(self):
        return self.on_hand - self.reserved

    def clean(self):
        if self.reserved > self.on_hand:
            raise ValidationError(
                {"reserved": "Reserved stock cannot exceed on-hand stock."}
            )

    def __str__(self):
        return f"Inventory - {self.seller_product}"