import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.catalog.models.product import Product
from apps.vehicles.models.variant import VehicleVariant


class CompatibilityStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ProductCompatibility(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="compatibilities",
    )

    vehicle_variant = models.ForeignKey(
        VehicleVariant,
        on_delete=models.PROTECT,
        related_name="product_compatibilities",
    )

    status = models.CharField(
        max_length=20,
        choices=CompatibilityStatus.choices,
        default=CompatibilityStatus.PENDING,
        db_index=True,
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product", "vehicle_variant"]

        constraints = [
            models.UniqueConstraint(
                fields=["product", "vehicle_variant"],
                name="unique_product_vehicle_compatibility",
            ),
        ]

        indexes = [
            models.Index(
                fields=["product", "status"],
            ),
            models.Index(
                fields=["vehicle_variant", "status"],
            ),
        ]

    def clean(self):
        super().clean()

        if self.product_id and not self.product.is_active:
            raise ValidationError(
                {"product": "Product is not active."}
            )

    def __str__(self):
        return (
            f"{self.product.name} - "
            f"{self.vehicle_variant}"
        )