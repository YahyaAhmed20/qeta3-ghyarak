import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.orders.models.order import Order


class OrderItem(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="items",
    )

    seller_product = models.ForeignKey(
        "stores.SellerProduct",
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    product_name_snapshot = models.CharField(
        max_length=255,
    )

    part_number_snapshot = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    quantity = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["order", "created_at"]),
            models.Index(fields=["seller_product"]),
        ]

    @property
    def subtotal(self):
        unit_price = Decimal(str(self.unit_price))
        discount = Decimal(str(self.discount))

        return (unit_price * self.quantity) - discount

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError(
                {"quantity": "Quantity must be greater than zero."}
            )

        if self.unit_price <= 0:
            raise ValidationError(
                {"unit_price": "Unit price must be greater than zero."}
            )

        if self.discount < 0:
            raise ValidationError(
                {"discount": "Discount cannot be negative."}
            )

        if self.discount > self.unit_price * self.quantity:
            raise ValidationError(
                {"discount": "Discount cannot exceed item total."}
            )

        if self.order.store_id != self.seller_product.store_id:
            raise ValidationError(
                {
                    "seller_product":
                    "Seller product must belong to the same store as the order."
                }
            )

    def __str__(self):
        return f"{self.product_name_snapshot} x {self.quantity}"