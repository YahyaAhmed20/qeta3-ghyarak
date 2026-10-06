from django.db import models
class InventoryMovementType(models.TextChoices):
    RESTOCK = "RESTOCK", "إضافة مخزون"
    SALE = "SALE", "بيع"
    RESERVATION = "RESERVATION", "حجز"
    RELEASE = "RELEASE", "إلغاء الحجز"
    RETURN = "RETURN", "مرتجع"
    ADJUSTMENT = "ADJUSTMENT", "تعديل المخزون"