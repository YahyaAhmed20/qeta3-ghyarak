from rest_framework import serializers

from apps.inventory.models import (
    Inventory,
    InventoryMovement,
)


class SellerInventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="seller_product.product.name",
        read_only=True,
    )

    brand_name = serializers.CharField(
        source="seller_product.product.brand.name",
        read_only=True,
    )

    category_name = serializers.CharField(
        source="seller_product.product.category.name",
        read_only=True,
    )

    seller_sku = serializers.CharField(
        source="seller_product.seller_sku",
        read_only=True,
    )

    price = serializers.DecimalField(
        source="seller_product.price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    sale_price = serializers.DecimalField(
        source="seller_product.sale_price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    available_stock = serializers.IntegerField(
        source="available",
        read_only=True,
    )

    is_active = serializers.BooleanField(
        source="seller_product.is_active",
        read_only=True,
    )

    class Meta:
        model = Inventory
        fields = [
            "id",
            "seller_product",
            "product_name",
            "brand_name",
            "category_name",
            "seller_sku",
            "price",
            "sale_price",
            "on_hand",
            "reserved",
            "available_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class InventoryRestockSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(
        min_value=1,
    )

    note = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class InventoryMovementSerializer(serializers.ModelSerializer):
    movement_type_label = serializers.CharField(
        source="get_movement_type_display",
        read_only=True,
    )

    created_by_phone = serializers.CharField(
        source="created_by.phone",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = InventoryMovement
        fields = [
            "id",
            "inventory",
            "movement_type",
            "movement_type_label",
            "quantity",
            "reference_type",
            "reference_id",
            "note",
            "created_by",
            "created_by_phone",
            "created_at",
        ]
        read_only_fields = fields