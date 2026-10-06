from rest_framework import serializers

from apps.marketplace.selectors.product import MarketplaceProductSelector


class MarketplaceSellerSerializer(serializers.Serializer):
    seller_product_id = serializers.UUIDField(source="id")
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

    min_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    sellers = serializers.SerializerMethodField()

    def get_sellers(self, obj):
        seller_products = obj.seller_products.all()

        return MarketplaceSellerSerializer(
            seller_products,
            many=True,
        ).data
        
        
class MarketplacePartNumberSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    part_number = serializers.CharField()
    number_type = serializers.CharField()
    brand = serializers.CharField(
        source="brand.name",
        allow_null=True,
    )


class MarketplaceCompatibilitySerializer(serializers.Serializer):
    id = serializers.UUIDField()

    make = serializers.CharField(
        source="vehicle_variant.engine.generation.model.make.name",
    )

    model = serializers.CharField(
        source="vehicle_variant.engine.generation.model.name",
    )

    generation = serializers.CharField(
        source="vehicle_variant.engine.generation.name",
    )

    engine = serializers.CharField(
        source="vehicle_variant.engine.name",
    )

    variant = serializers.CharField(
        source="vehicle_variant.name",
    )

    transmission = serializers.CharField(
        source="vehicle_variant.transmission",
    )

    market = serializers.CharField(
        source="vehicle_variant.market",
    )

    notes = serializers.CharField()


class MarketplaceProductDetailSerializer(serializers.Serializer):
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

    min_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    part_numbers = MarketplacePartNumberSerializer(
        many=True,
        read_only=True,
    )

    compatibilities = MarketplaceCompatibilitySerializer(
        many=True,
        read_only=True,
    )

    sellers = serializers.SerializerMethodField()

    def get_sellers(self, obj):
        seller_products = obj.seller_products.all()

        return MarketplaceSellerSerializer(
            seller_products,
            many=True,
        ).data