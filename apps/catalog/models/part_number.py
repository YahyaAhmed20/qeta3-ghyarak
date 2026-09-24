import uuid

from django.core.exceptions import ValidationError
from django.db import models

from .brand import Brand
from .product import Product


class PartNumberType(models.TextChoices):
    OEM = "OEM", "OEM"
    MANUFACTURER = "MANUFACTURER", "Manufacturer"
    CROSS_REFERENCE = "CROSS_REFERENCE", "Cross Reference"
    AFTERMARKET = "AFTERMARKET", "Aftermarket"


class ProductPartNumber(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="part_numbers",
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="part_numbers",
        null=True,
        blank=True,
    )

    part_number = models.CharField(
        max_length=100,
    )

    normalized_part_number = models.CharField(
        max_length=100,
        db_index=True,
        editable=False,
    )

    number_type = models.CharField(
        max_length=30,
        choices=PartNumberType.choices,
        default=PartNumberType.MANUFACTURER,
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
        ordering = ["part_number"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "product",
                    "normalized_part_number",
                    "number_type",
                    "brand",
                ],
                name="unique_product_part_number",
            ),
        ]

        indexes = [
            models.Index(
                fields=["normalized_part_number", "is_active"],
            ),
            models.Index(
                fields=["product", "is_active"],
            ),
            models.Index(
                fields=["brand", "is_active"],
            ),
        ]

    def normalize_part_number(self):
        return "".join(
            character
            for character in self.part_number.upper().strip()
            if character.isalnum()
        )

    def clean_fields(self, exclude=None):
        self.normalized_part_number = self.normalize_part_number()
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()

        normalized = self.normalize_part_number()

        if not normalized:
            raise ValidationError(
                {"part_number": "Part number cannot be empty."}
            )

        self.normalized_part_number = normalized

        duplicate_exists = (
            ProductPartNumber.objects
            .filter(
                product=self.product,
                normalized_part_number=normalized,
                number_type=self.number_type,
                brand=self.brand,
            )
            .exclude(pk=self.pk)
            .exists()
        )

        if duplicate_exists:
            raise ValidationError(
                {
                    "part_number": (
                        "This part number already exists for this product."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.normalized_part_number = self.normalize_part_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.part_number