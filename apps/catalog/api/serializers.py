from rest_framework import serializers

from apps.catalog.models import (
    Brand,
    Category,
    CompatibilityStatus,
    Product,
    ProductCompatibility,
)


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
    )

    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "brand",
            "name",
            "slug",
            "description",
            "product_type",
            "country_of_origin",
            "warranty",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ProductCompatibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCompatibility
        fields = [
            "id",
            "product",
            "vehicle_variant",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_product(self, product):
        if not product.is_active:
            raise serializers.ValidationError(
                "Product is not active."
            )

        return product

    def validate_vehicle_variant(self, vehicle_variant):
        if not vehicle_variant.is_active:
            raise serializers.ValidationError(
                "Vehicle variant is not active."
            )

        return vehicle_variant

    def validate(self, attrs):
        product = attrs.get(
            "product",
            getattr(self.instance, "product", None),
        )

        vehicle_variant = attrs.get(
            "vehicle_variant",
            getattr(self.instance, "vehicle_variant", None),
        )

        queryset = ProductCompatibility.objects.filter(
            product=product,
            vehicle_variant=vehicle_variant,
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "This product is already linked to this vehicle variant."
                    ]
                }
            )

        return attrs