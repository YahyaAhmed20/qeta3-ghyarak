from rest_framework import serializers

from apps.marketplace.selectors.product import MarketplaceProductSelector


class MarketplaceSellerSerializer(serializers.Serializer):
    store_name = serializers.CharField(source="store.name")
    city = serializers.CharField(source="store.city")
    price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    sale_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        allow_null=True,
    )
    available = serializers.IntegerField(
        source="inventory.available",
    )


class MarketplaceProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField()
    product_type = serializers.CharField()
    country_of_origin = serializers.CharField()
    warranty = serializers.CharField()

    brand = serializers.CharField(
        source="brand.name",
        allow_null=True,
    )

    category = serializers.CharField(
        source="category.name",
    )

    sellers = serializers.SerializerMethodField()

    def get_sellers(self, obj):
        seller_products = obj.seller_products.all()

        return MarketplaceSellerSerializer(
            seller_products,
            many=True,
        ).data