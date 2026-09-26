import uuid

from django.db import models


class DeliveryOTP(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="delivery_otps",
    )

    code_hash = models.CharField(max_length=128)

    status = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVE", "Active"),
            ("VERIFIED", "Verified"),
            ("EXPIRED", "Expired"),
            ("BLOCKED", "Blocked"),
        ],
        default="ACTIVE",
        db_index=True,
    )

    attempts = models.PositiveSmallIntegerField(default=0)

    max_attempts = models.PositiveSmallIntegerField(default=5)

    expires_at = models.DateTimeField()

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self):
        return f"Delivery OTP - {self.order.order_number}"