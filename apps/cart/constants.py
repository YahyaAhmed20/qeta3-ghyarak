from django.db import models


class CartStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    CONVERTED = "CONVERTED", "Converted"
    ABANDONED = "ABANDONED", "Abandoned"