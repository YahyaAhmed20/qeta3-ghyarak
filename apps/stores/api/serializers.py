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
    class Meta:
        model = SellerProduct
        fields = [
            "id",
            "store",
            "product",
            "seller_sku",
            "price",
            "sale_price",
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

        try:
            return SellerProductService.create_seller_product(
                store=store,
                **validated_data,
            )
        except ValueError as exc:
            raise serializers.ValidationError(
                {"detail": str(exc)}
            ) from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict
            ) from exc