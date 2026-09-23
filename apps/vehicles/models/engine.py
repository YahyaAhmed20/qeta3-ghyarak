import uuid

from django.db import models

from .generation import VehicleGeneration


class VehicleEngine(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    generation = models.ForeignKey(
        VehicleGeneration,
        on_delete=models.PROTECT,
        related_name="engines",
    )

    name = models.CharField(
        max_length=150,
    )

    code = models.CharField(
        max_length=100,
        blank=True,
    )

    displacement_cc = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    fuel_type = models.CharField(
        max_length=50,
        blank=True,
    )

    power_hp = models.PositiveSmallIntegerField(
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
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["generation", "name"],
                name="unique_vehicle_engine_per_generation",
            ),
            models.UniqueConstraint(
                fields=["generation", "code"],
                name="unique_vehicle_engine_code_per_generation",
            ),
        ]
        indexes = [
            models.Index(
                fields=["generation", "is_active"],
            ),
        ]

    def __str__(self):
        return f"{self.generation} - {self.name}"