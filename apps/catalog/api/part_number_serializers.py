from rest_framework import serializers

from apps.catalog.models import (
    Brand,
    Product,
    ProductPartNumber,
)

from apps.catalog.services.part_number import PartNumberService


class ProductPartNumberSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
    )

    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = ProductPartNumber
        fields = [
            "id",
            "product",
            "brand",
            "part_number",
            "normalized_part_number",
            "number_type",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "normalized_part_number",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        product = attrs.get(
            "product",
            getattr(self.instance, "product", None),
        )

        brand = attrs.get(
            "brand",
            getattr(self.instance, "brand", None),
        )

        part_number = attrs.get(
            "part_number",
            getattr(self.instance, "part_number", None),
        )

        number_type = attrs.get(
            "number_type",
            getattr(self.instance, "number_type", None),
        )

        if product is not None and part_number:
            normalized = "".join(
                character
                for character in part_number.upper().strip()
                if character.isalnum()
            )

            duplicate = (
                ProductPartNumber.objects
                .filter(
                    product=product,
                    normalized_part_number=normalized,
                    number_type=number_type,
                    brand=brand,
                )
                .exclude(
                    pk=self.instance.pk if self.instance else None
                )
                .exists()
            )

            if duplicate:
                raise serializers.ValidationError(
                    {
                        "part_number": (
                            "This part number already exists "
                            "for this product."
                        )
                    }
                )

        return attrs

    def create(self, validated_data):
        return PartNumberService.create_part_number(
            **validated_data
        )

    def update(self, instance, validated_data):
        return PartNumberService.update_part_number(
            part_number_id=instance.id,
            **validated_data
        )