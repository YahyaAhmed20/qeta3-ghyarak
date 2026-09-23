from django.db import models


class UserRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Customer"

    SELLER_OWNER = "SELLER_OWNER", "Seller Owner"
    SELLER_MANAGER = "SELLER_MANAGER", "Seller Manager"
    SELLER_STAFF = "SELLER_STAFF", "Seller Staff"

    DELIVERY = "DELIVERY", "Delivery"

    SUPPORT = "SUPPORT", "Support"

    ADMIN = "ADMIN", "Admin"
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"


class UserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"


class OTPPurpose(models.TextChoices):
    LOGIN = "LOGIN", "Login"
    PHONE_VERIFICATION = "PHONE_VERIFICATION", "Phone Verification"
    PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"