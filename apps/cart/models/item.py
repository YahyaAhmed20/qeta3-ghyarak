import uuid

from django.core.exceptions import ValidationError
from django.db import models


class CartItem(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    cart = models.ForeignKey(
        "cart.Cart",
        on_delete=models.PROTECT,
        related_name="items",
    )

    seller_product = models.ForeignKey(
        "stores.SellerProduct",
        on_delete=models.PROTECT,
        related_name="cart_items",
    )

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "seller_product"],
                name="unique_cart_seller_product",
            ),
        ]
        indexes = [
            models.Index(
                fields=["cart", "created_at"],
            ),
            models.Index(
                fields=["seller_product"],
            ),
        ]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError(
                {"quantity": "Quantity must be greater than zero."}
            )

        if self.unit_price <= 0:
            raise ValidationError(
                {"unit_price": "Unit price must be greater than zero."}
            )

        if self.cart.store_id != self.seller_product.store_id:
            raise ValidationError(
                {
                    "seller_product": (
                        "Seller product must belong to the same store as the cart."
                    )
                }
            )

        if not self.seller_product.is_active:
            raise ValidationError(
                {"seller_product": "Seller product must be active."}
            )

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.seller_product.product.name} x {self.quantity}"