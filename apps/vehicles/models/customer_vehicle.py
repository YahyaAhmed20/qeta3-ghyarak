import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .variant import VehicleVariant
from apps.common.normalizers import normalize_vin


class CustomerVehicle(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles",
    )

    vehicle_variant = models.ForeignKey(
        VehicleVariant,
        on_delete=models.PROTECT,
        related_name="customer_vehicles",
    )

    nickname = models.CharField(
        max_length=100,
        blank=True,
    )

    plate_number = models.CharField(
        max_length=30,
        blank=True,
    )

    vin = models.CharField(
        max_length=17,
        blank=True,
    )

    is_default = models.BooleanField(
        default=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_default=True),
                name="unique_default_vehicle_per_customer",
            ),
            models.UniqueConstraint(
                fields=["customer", "vehicle_variant"],
                name="unique_customer_vehicle_variant",
            ),
        ]
        indexes = [
            models.Index(
                fields=["customer", "is_default"],
            ),
            models.Index(
                fields=["vehicle_variant"],
            ),
        ]

    def clean(self):
        if self.vin:
            normalized_vin = normalize_vin(self.vin)

            if len(normalized_vin) != 17:
                raise ValidationError(
                    {"vin": "VIN must contain exactly 17 characters."}
                )

            self.vin = normalized_vin

    def __str__(self):
        if self.nickname:
            return self.nickname

        return f"{self.customer} - {self.vehicle_variant}"