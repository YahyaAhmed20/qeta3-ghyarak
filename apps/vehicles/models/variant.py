import uuid

from django.db import models

from .engine import VehicleEngine


class VehicleVariant(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    engine = models.ForeignKey(
        VehicleEngine,
        on_delete=models.PROTECT,
        related_name="variants",
    )

    name = models.CharField(
        max_length=150,
    )

    slug = models.SlugField(
        max_length=180,
    )

    transmission = models.CharField(
        max_length=50,
        blank=True,
    )

    market = models.CharField(
        max_length=50,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["engine", "name"],
                name="unique_vehicle_variant",
            ),
            models.UniqueConstraint(
                fields=["engine", "slug"],
                name="unique_vehicle_variant_slug",
            ),
        ]
        indexes = [
            models.Index(
                fields=["engine", "is_active"],
            ),
        ]

    def __str__(self):
        return f"{self.engine} - {self.name}"