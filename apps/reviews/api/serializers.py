from rest_framework import serializers

from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    customer_id = serializers.UUIDField(
        source="customer.id",
        read_only=True,
    )

    store_id = serializers.UUIDField(
        source="store.id",
        read_only=True,
    )

    product_id = serializers.UUIDField(
        source="product.id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "order",
            "customer_id",
            "store_id",
            "product_id",
            "rating",
            "comment",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_id",
            "store_id",
            "product_id",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value

    def validate_comment(self, value):
        return value.strip()