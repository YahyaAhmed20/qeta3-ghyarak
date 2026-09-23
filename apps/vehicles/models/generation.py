import uuid

from django.db import models

from .model import VehicleModel


class VehicleGeneration(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    model = models.ForeignKey(
        VehicleModel,
        on_delete=models.PROTECT,
        related_name="generations",
    )

    name = models.CharField(
        max_length=150,
    )

    slug = models.SlugField(
        max_length=180,
    )

    year_from = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    year_to = models.PositiveSmallIntegerField(
        null=True,
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
        ordering = ["year_from", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["model", "name"],
                name="unique_vehicle_generation_per_model",
            ),
            models.UniqueConstraint(
                fields=["model", "slug"],
                name="unique_vehicle_generation_slug_per_model",
            ),
        ]
        indexes = [
            models.Index(
                fields=["model", "is_active"],
            ),
        ]

    def __str__(self):
        return f"{self.model} {self.name}"