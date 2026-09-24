import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        null=True,
        blank=True,
    )

    name = models.CharField(
        max_length=150,
    )

    slug = models.SlugField(
        max_length=180,
    )

    description = models.TextField(
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
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"],
                name="unique_category_name_per_parent",
            ),
            models.UniqueConstraint(
                fields=["parent", "slug"],
                name="unique_category_slug_per_parent",
            ),
        ]
        indexes = [
            models.Index(
                fields=["parent", "is_active"],
            ),
        ]

    def clean(self):
        if self.parent_id == self.id:
            raise ValidationError(
                {"parent": "A category cannot be its own parent."}
            )

    def __str__(self):
        return self.name