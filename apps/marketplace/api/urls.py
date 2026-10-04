from django.urls import path

from apps.marketplace.api.views import MarketplaceProductListAPIView


urlpatterns = [
    path(
        "products/",
        MarketplaceProductListAPIView.as_view(),
        name="marketplace-product-list",
    ),
]