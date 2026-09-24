from django.db import models


class InventoryMovementType(models.TextChoices):
    RESTOCK = "RESTOCK", "Restock"
    SALE = "SALE", "Sale"
    RESERVATION = "RESERVATION", "Reservation"
    RELEASE = "RELEASE", "Release"
    RETURN = "RETURN", "Return"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"