import uuid

from django.db import models

from .brand import Brand
from .category import Category


class ProductType(models.TextChoices):
    ORIGINAL = "ORIGINAL", "Original"
    OEM = "OEM", "OEM"
    AFTERMARKET = "AFTERMARKET", "Aftermarket"
    USED = "USED", "Used"


class Product(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )

    name = models.CharField(
        max_length=250,
    )

    slug = models.SlugField(
        max_length=280,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.AFTERMARKET,
    )

    country_of_origin = models.CharField(
        max_length=100,
        blank=True,
    )

    warranty = models.CharField(
        max_length=150,
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
        ordering = ["name"]
        indexes = [
            models.Index(
                fields=["category", "is_active"],
            ),
            models.Index(
                fields=["brand", "is_active"],
            ),
            models.Index(
                fields=["product_type", "is_active"],
            ),
        ]

    def __str__(self):
        return self.name