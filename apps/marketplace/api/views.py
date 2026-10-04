from rest_framework import generics
from rest_framework.permissions import AllowAny
from apps.marketplace.api.pagination import MarketplaceProductPagination
from apps.marketplace.api.serializers import MarketplaceProductSerializer
from apps.marketplace.selectors.product import MarketplaceProductSelector
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound

from apps.marketplace.api.pagination import MarketplaceProductPagination
from apps.marketplace.api.serializers import (
    MarketplaceProductDetailSerializer,
    MarketplaceProductSerializer,
)
from apps.marketplace.selectors.product import MarketplaceProductSelector

class MarketplaceProductListAPIView(generics.ListAPIView):
    serializer_class = MarketplaceProductSerializer
    permission_classes = [AllowAny]
    pagination_class = MarketplaceProductPagination

    def get_queryset(self):
        search = self.request.query_params.get("search")
        category_id = self.request.query_params.get("category")
        brand_id = self.request.query_params.get("brand")
        vehicle_id = self.request.query_params.get("vehicle")
        ordering = self.request.query_params.get("ordering")


        return MarketplaceProductSelector.get_products(
            search=search,
            category_id=category_id,
            brand_id=brand_id,
            vehicle_id=vehicle_id,
            ordering=ordering
        )
        
class MarketplaceProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = MarketplaceProductDetailSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        product_id = self.kwargs["product_id"]

        product = MarketplaceProductSelector.get_product_detail(
            product_id=product_id,
        )

        if product is None:
            raise NotFound("Product not found.")

        return product