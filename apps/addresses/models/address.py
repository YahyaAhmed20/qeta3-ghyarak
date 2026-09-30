import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Address(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="addresses",
    )

    label = models.CharField(
        max_length=50,
    )

    recipient_name = models.CharField(
        max_length=150,
    )

    phone = models.CharField(
        max_length=20,
    )

    city = models.CharField(
        max_length=100,
    )

    area = models.CharField(
        max_length=100,
    )

    address_line = models.CharField(
        max_length=255,
    )

    building = models.CharField(
        max_length=50,
        blank=True,
    )

    floor = models.CharField(
        max_length=20,
        blank=True,
    )

    apartment = models.CharField(
        max_length=20,
        blank=True,
    )

    landmark = models.CharField(
        max_length=255,
        blank=True,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-90),
            MaxValueValidator(90),
        ],
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-180),
            MaxValueValidator(180),
        ],
    )

    is_default = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "addresses"
        ordering = ["-is_default", "-created_at"]
        indexes = [
            models.Index(
                fields=["customer", "is_default"],
                name="addresses_customer_default_idx",
            ),
            models.Index(
                fields=["customer", "created_at"],
                name="addresses_customer_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.label} - {self.recipient_name}"