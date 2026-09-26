from django.db import models


class OrderStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    ACCEPTED = "ACCEPTED", "Accepted"
    PREPARING = "PREPARING", "Preparing"
    READY = "READY", "Ready"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY", "Out for Delivery"
    DELIVERED = "DELIVERED", "Delivered"

    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"
    FAILED_DELIVERY = "FAILED_DELIVERY", "Failed Delivery"
    RETURNED = "RETURNED", "Returned"
    REFUNDED = "REFUNDED", "Refunded"
    
    
class DeliveryOTPStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    VERIFIED = "VERIFIED", "Verified"
    EXPIRED = "EXPIRED", "Expired"
    BLOCKED = "BLOCKED", "Blocked"
    
    
class DeliveryAssignmentStatus(models.TextChoices):
    ASSIGNED = "ASSIGNED", "Assigned"
    ACCEPTED = "ACCEPTED", "Accepted"
    DELIVERED = "DELIVERED", "Delivered"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"