import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.cart.constants import CartStatus


class Cart(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="carts",
    )

    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.PROTECT,
        related_name="carts",
    )

    status = models.CharField(
        max_length=20,
        choices=CartStatus.choices,
        default=CartStatus.ACTIVE,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(status=CartStatus.ACTIVE),
                name="unique_active_cart_per_customer",
            ),
        ]
        indexes = [
            models.Index(
                fields=["customer", "status"],
            ),
            models.Index(
                fields=["store", "status"],
            ),
        ]

    def clean(self):
        if self.customer.role != "CUSTOMER":
            raise ValidationError(
                {"customer": "Cart customer must have CUSTOMER role."}
            )

        if self.store.status != "ACTIVE" or not self.store.is_verified:
            raise ValidationError(
                {"store": "Cart store must be active and verified."}
            )

    def __str__(self):
        return f"Cart {self.id} - {self.customer.phone}"