import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class StoreStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    REJECTED = "REJECTED", "Rejected"


class Store(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_stores",
    )

    name = models.CharField(
        max_length=200,
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=StoreStatus.choices,
        default=StoreStatus.PENDING,
        db_index=True,
    )

    is_verified = models.BooleanField(
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
        ordering = ["name"]
        indexes = [
            models.Index(
                fields=["owner", "status"],
            ),
            models.Index(
                fields=["city", "status"],
            ),
            models.Index(
                fields=["status", "is_verified"],
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner"],
                name="unique_store_per_owner",
            ),
        ]

    def clean(self):
        super().clean()

        if self.owner_id and self.owner.role not in {
            "SELLER_OWNER",
            "ADMIN",
            "SUPER_ADMIN",
        }:
            raise ValidationError(
                {
                    "owner": (
                        "Store owner must have a seller owner role."
                    )
                }
            )

    def __str__(self):
        return self.name