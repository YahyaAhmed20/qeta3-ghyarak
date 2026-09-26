from rest_framework import serializers

from apps.accounts.models import User


class DeliveryAssignmentCreateSerializer(serializers.Serializer):
    delivery_user_id = serializers.UUIDField()

    def validate_delivery_user_id(self, value):
        try:
            user = User.objects.get(
                id=value,
                role="DELIVERY",
                is_active=True,
            )
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Delivery user not found."
            )

        return user