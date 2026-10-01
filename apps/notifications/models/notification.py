import uuid

from django.conf import settings
from django.db import models

from apps.notifications.constants import NOTIFICATION_TYPES


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        ORDER_CREATED = (
            "ORDER_CREATED",
            NOTIFICATION_TYPES["ORDER_CREATED"],
        )
        ORDER_ACCEPTED = (
            "ORDER_ACCEPTED",
            NOTIFICATION_TYPES["ORDER_ACCEPTED"],
        )
        ORDER_REJECTED = (
            "ORDER_REJECTED",
            NOTIFICATION_TYPES["ORDER_REJECTED"],
        )
        ORDER_PREPARING = (
            "ORDER_PREPARING",
            NOTIFICATION_TYPES["ORDER_PREPARING"],
        )
        ORDER_READY = (
            "ORDER_READY",
            NOTIFICATION_TYPES["ORDER_READY"],
        )
        ORDER_OUT_FOR_DELIVERY = (
            "ORDER_OUT_FOR_DELIVERY",
            NOTIFICATION_TYPES["ORDER_OUT_FOR_DELIVERY"],
        )
        ORDER_DELIVERED = (
            "ORDER_DELIVERED",
            NOTIFICATION_TYPES["ORDER_DELIVERED"],
        )
        ORDER_CANCELLED = (
            "ORDER_CANCELLED",
            NOTIFICATION_TYPES["ORDER_CANCELLED"],
        )
        REVIEW_CREATED = (
            "REVIEW_CREATED",
            NOTIFICATION_TYPES["REVIEW_CREATED"],
        )
        SETTLEMENT_READY = (
            "SETTLEMENT_READY",
            NOTIFICATION_TYPES["SETTLEMENT_READY"],
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="notifications",
    )

    type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )

    title = models.CharField(
        max_length=150,
    )

    message = models.TextField(
        max_length=1000,
    )

    data = models.JSONField(
        default=dict,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    read_at = models.DateTimeField(
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
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
        models.Index(
            fields=["recipient", "is_read"],
            name="notif_recipient_read_idx",
        ),
        models.Index(
            fields=["recipient", "created_at"],
            name="notif_recipient_created_idx",
        ),
        models.Index(
            fields=["type", "created_at"],
            name="notif_type_created_idx",
        ),
    ]
    def __str__(self):
        return f"{self.recipient.phone} - {self.title}"