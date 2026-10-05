from rest_framework.permissions import BasePermission

from apps.accounts.constants import UserRole


class IsSellerOwner(BasePermission):
    message = "Only seller owners can access the seller dashboard."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.status == "ACTIVE"
            and request.user.role == UserRole.SELLER_OWNER
        )