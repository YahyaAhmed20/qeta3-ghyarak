from django.db import models


class CommissionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    READY = "READY", "Ready"
    SETTLED = "SETTLED", "Settled"
    DISPUTED = "DISPUTED", "Disputed"
    CANCELLED = "CANCELLED", "Cancelled"