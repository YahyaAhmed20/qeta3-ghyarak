import uuid

from django.db import models

from .make import VehicleMake


class VehicleModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    make = models.ForeignKey(
        VehicleMake,
        on_delete=models.PROTECT,
        related_name="models",
    )

    name = models.CharField(
        max_length=100,
    )

    slug = models.SlugField(
        max_length=120,
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
                fields=["make", "name"],
                name="unique_vehicle_model_per_make",
            ),
            models.UniqueConstraint(
                fields=["make", "slug"],
                name="unique_vehicle_model_slug_per_make",
            ),
        ]
        indexes = [
            models.Index(
                fields=["make", "is_active"],
            ),
        ]

    def __str__(self):
        return f"{self.make.name} {self.name}"