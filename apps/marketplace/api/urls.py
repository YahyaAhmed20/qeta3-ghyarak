from django.urls import path

from apps.marketplace.api.views import MarketplaceProductListAPIView
from apps.marketplace.api.views import (
    MarketplaceProductDetailAPIView,
    MarketplaceProductListAPIView,
)
urlpatterns = [
    path(
        "products/",
        MarketplaceProductListAPIView.as_view(),
        name="marketplace-product-list",
    ),
    path(
        "products/<uuid:product_id>/",
        MarketplaceProductDetailAPIView.as_view(),
        name="marketplace-product-detail",
    ),
]