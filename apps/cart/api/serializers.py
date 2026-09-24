from decimal import Decimal

from rest_framework import serializers

from apps.cart.models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="seller_product.product.name",
        read_only=True,
    )

    seller_product_id = serializers.UUIDField(
        source="seller_product.id",
        read_only=True,
    )

    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "seller_product_id",
            "product_name",
            "quantity",
            "unit_price",
            "subtotal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "seller_product_id",
            "product_name",
            "unit_price",
            "subtotal",
            "created_at",
            "updated_at",
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "store",
            "status",
            "items",
            "items_count",
            "subtotal",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_items_count(self, obj):
        return obj.items.count()

    def get_subtotal(self, obj):
        return sum(
            (item.subtotal for item in obj.items.all()),
            Decimal("0.00"),
        )


class CartItemWriteSerializer(serializers.Serializer):
    seller_product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)