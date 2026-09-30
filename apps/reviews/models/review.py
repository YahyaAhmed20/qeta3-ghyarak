import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.constants import UserRole
from apps.catalog.models import Product
from apps.orders.constants import OrderStatus
from apps.orders.models import Order
from apps.stores.models import Store

from apps.reviews.constants import ReviewStatus


class Review(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="reviews",
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviews",
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="reviews",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="reviews",
        null=True,
        blank=True,
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    comment = models.TextField(
        blank=True,
        max_length=1000,
    )

    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["store", "status"],
                name="reviews_store_status_idx",
            ),
            models.Index(
                fields=["product", "status"],
                name="reviews_product_status_idx",
            ),
            models.Index(
                fields=["customer", "created_at"],
                name="reviews_customer_created_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "customer", "store"],
                name="unique_store_review_per_order",
            ),
            models.UniqueConstraint(
                fields=["order", "customer", "product"],
                name="unique_product_review_per_order",
            ),
        ]

    def clean(self):
        errors = {}

        if self.customer_id and self.order_id:
            if self.order.customer_id != self.customer_id:
                errors["customer"] = (
                    "Customer must be the owner of the order."
                )

        if self.store_id and self.order_id:
            if self.order.store_id != self.store_id:
                errors["store"] = (
                    "Store must belong to the order."
                )

        if self.customer_id:
            if self.customer.role != UserRole.CUSTOMER:
                errors["customer"] = (
                    "Only customers can create reviews."
                )

        if self.order_id:
            if self.order.status != OrderStatus.DELIVERED:
                errors["order"] = (
                    "Reviews can only be created for delivered orders."
                )

        if self.product_id and self.order_id:
            product_in_order = self.order.items.filter(
                seller_product__product_id=self.product_id,
                seller_product__store_id=self.store_id,
            ).exists()

            if not product_in_order:
                errors["product"] = (
                    "Product must belong to the order and its store."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        target = self.product.name if self.product else self.store.name
        return f"{self.customer.phone} - {target} - {self.rating}"