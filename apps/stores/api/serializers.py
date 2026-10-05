from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.stores.models import SellerProduct, Store
from apps.stores.services.seller_product import SellerProductService
from apps.stores.services.store import StoreService


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            "id",
            "owner",
            "name",
            "slug",
            "description",
            "phone",
            "address",
            "city",
            "latitude",
            "longitude",
            "status",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "status",
            "is_verified",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required."
            )

        try:
            return StoreService.create_store(
                owner=request.user,
                **validated_data,
            )
        except ValueError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc

    def update(self, instance, validated_data):
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication is required."
            )

        try:
            return StoreService.update_store(
                store_id=instance.id,
                owner=request.user,
                **validated_data,
            )
        except ValueError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc


class SellerProductSerializer(serializers.ModelSerializer):
    initial_stock = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=0,
        default=0,
    )

    class Meta:
        model = SellerProduct
        fields = [
            "id",
            "store",
            "product",
            "seller_sku",
            "price",
            "sale_price",
            "initial_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "store",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        store = self.context.get("store")

        if store is None:
            raise serializers.ValidationError(
                {"detail": "Store context is required."}
            )

        initial_stock = validated_data.pop("initial_stock", 0)

        try:
            seller_product, inventory = (
                SellerProductService.create_seller_product_with_inventory(
                    store=store,
                    initial_stock=initial_stock,
                    user=self.context["request"].user,
                    **validated_data,
                )
            )

            return seller_product
        except ValueError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict
            ) from exc


class SellerDashboardProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )
    brand_name = serializers.CharField(
        source="product.brand.name",
        read_only=True,
        allow_null=True,
    )
    category_name = serializers.CharField(
        source="product.category.name",
        read_only=True,
    )
    stock = serializers.IntegerField(
        source="inventory.on_hand",
        read_only=True,
    )
    reserved_stock = serializers.IntegerField(
        source="inventory.reserved",
        read_only=True,
    )
    available_stock = serializers.IntegerField(
        source="inventory.available",
        read_only=True,
    )
    inventory_id = serializers.UUIDField(
        source="inventory.id",
        read_only=True,
    )

    class Meta:
        model = SellerProduct
        fields = [
            "id",
            "product",
            "product_name",
            "brand_name",
            "category_name",
            "seller_sku",
            "price",
            "sale_price",
            "stock",
            "reserved_stock",
            "available_stock",
            "inventory_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "product",
            "product_name",
            "brand_name",
            "category_name",
            "stock",
            "reserved_stock",
            "available_stock",
            "inventory_id",
            "is_active",
            "created_at",
            "updated_at",
        ]