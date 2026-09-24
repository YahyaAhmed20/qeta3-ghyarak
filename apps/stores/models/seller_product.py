import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.catalog.models.product import Product
from apps.stores.models.store import Store


class SellerProduct(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="seller_products",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="seller_products",
    )

    seller_sku = models.CharField(
        max_length=100,
        blank=True,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    sale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["product__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["store", "product"],
                name="unique_store_product",
            ),
        ]
        indexes = [
            models.Index(
                fields=["store", "is_active"],
            ),
            models.Index(
                fields=["product", "is_active"],
            ),
        ]

    def clean(self):
        super().clean()

        if self.store_id and self.store.status != "ACTIVE":
            raise ValidationError(
                {"store": "Store must be active."}
            )

        if self.product_id and not self.product.is_active:
            raise ValidationError(
                {"product": "Product must be active."}
            )

        if self.price <= 0:
            raise ValidationError(
                {"price": "Price must be greater than zero."}
            )

        if self.sale_price is not None:
            if self.sale_price <= 0:
                raise ValidationError(
                    {"sale_price": "Sale price must be greater than zero."}
                )

            if self.sale_price > self.price:
                raise ValidationError(
                    {"sale_price": "Sale price cannot be greater than price."}
                )

    def __str__(self):
        return f"{self.store.name} - {self.product.name}"