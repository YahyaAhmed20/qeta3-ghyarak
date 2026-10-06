from rest_framework import serializers

from apps.accounts.models import User
from rest_framework import serializers

from apps.orders.models import Order, OrderItem


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
    
    
class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.UUIDField()
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
    )
    
class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.UUIDField()
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
    )
    
class SellerOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product_name_snapshot",
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "seller_product",
            "product_name",
            "part_number_snapshot",
            "unit_price",
            "discount",
            "quantity",
            "subtotal",
        ]
        read_only_fields = fields


class SellerOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
    )
    customer_phone = serializers.CharField(
        source="customer.phone",
        read_only=True,
    )
    items = SellerOrderItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer_name",
            "customer_phone",
            "status",
            "subtotal",
            "seller_discount",
            "platform_discount",
            "delivery_fee",
            "total",
            "address_snapshot",
            "notes",
            "delivered_at",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = fields