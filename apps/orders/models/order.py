import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.orders.constants import OrderStatus


class Order(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order_number = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="orders",
    )

    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.CREATED,
        db_index=True,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    seller_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    platform_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    address_snapshot = models.JSONField(
        default=dict,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
        default="",
    )

    delivered_at = models.DateTimeField(
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
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["store", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def clean(self):
        if self.customer.role != "CUSTOMER":
            raise ValidationError(
                {"customer": "Order customer must have CUSTOMER role."}
            )

        if self.store.status != "ACTIVE" or not self.store.is_verified:
            raise ValidationError(
                {"store": "Order store must be active and verified."}
            )

        monetary_fields = {
            "subtotal": self.subtotal,
            "seller_discount": self.seller_discount,
            "platform_discount": self.platform_discount,
            "delivery_fee": self.delivery_fee,
            "total": self.total,
        }

        for field_name, value in monetary_fields.items():
            if value is not None and value < 0:
                raise ValidationError(
                    {field_name: "Amount cannot be negative."}
                )

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()

        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        return f"QG-{uuid.uuid4().hex[:12].upper()}"

    def __str__(self):
        return self.order_number