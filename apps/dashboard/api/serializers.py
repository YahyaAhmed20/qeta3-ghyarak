from rest_framework import serializers


class DashboardStoreSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    status = serializers.CharField()
    is_verified = serializers.BooleanField()


class DashboardOrdersSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    today = serializers.IntegerField()
    pending = serializers.IntegerField()
    delivered = serializers.IntegerField()


class DashboardSalesSerializer(serializers.Serializer):
    today = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class DashboardInventorySerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    out_of_stock = serializers.IntegerField()


class DashboardSettlementsSerializer(serializers.Serializer):
    pending = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    ready = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    processing = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class DashboardOverviewSerializer(serializers.Serializer):
    store = DashboardStoreSerializer()
    orders = DashboardOrdersSerializer()
    sales = DashboardSalesSerializer()
    inventory = DashboardInventorySerializer()
    settlements = DashboardSettlementsSerializer()