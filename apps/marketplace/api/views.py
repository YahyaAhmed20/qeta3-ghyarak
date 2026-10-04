from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.marketplace.api.serializers import MarketplaceProductSerializer
from apps.marketplace.selectors.product import MarketplaceProductSelector


class MarketplaceProductListAPIView(generics.ListAPIView):
    serializer_class = MarketplaceProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        search = self.request.query_params.get("search")
        category_id = self.request.query_params.get("category")
        brand_id = self.request.query_params.get("brand")
        vehicle_id = self.request.query_params.get("vehicle")

        return MarketplaceProductSelector.get_products(
            search=search,
            category_id=category_id,
            brand_id=brand_id,
            vehicle_id=vehicle_id,

        )