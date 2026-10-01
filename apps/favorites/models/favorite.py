import uuid

from django.conf import settings
from django.db import models


class Favorite(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="favorites",
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="favorites",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorites"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "product"],
                name="favorites_customer_product_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=["customer", "created_at"],
                name="favorites_customer_created_idx",
            ),
            models.Index(
                fields=["product", "created_at"],
                name="favorites_product_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.customer.phone} - {self.product.name}"