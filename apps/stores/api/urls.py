from django.urls import path

from apps.stores.api.views import (
    MyStoreDetailAPIView,
    MyStoreListAPIView,
    SellerProductActivateAPIView,
    SellerProductDeactivateAPIView,
    SellerProductDetailAPIView,
    SellerProductListCreateAPIView,
    StoreCreateAPIView,
    SellerDashboardProductListAPIView,
)

urlpatterns = [
    path(
        "",
        StoreCreateAPIView.as_view(),
        name="store-create",
    ),
    path(
        "<uuid:id>/",
        MyStoreDetailAPIView.as_view(),
        name="my-store-detail",
    ),
    path(
        "my/",
        MyStoreListAPIView.as_view(),
        name="my-stores",
    ),
    path(
        "products/",
        SellerProductListCreateAPIView.as_view(),
        name="seller-product-list-create",
    ),
    path(
        "products/<uuid:id>/deactivate/",
        SellerProductDeactivateAPIView.as_view(),
        name="seller-product-deactivate",
    ),
    path(
    "dashboard/products/",
    SellerDashboardProductListAPIView.as_view(),
    name="seller-dashboard-products",
),
    path(
        "products/<uuid:id>/activate/",
        SellerProductActivateAPIView.as_view(),
        name="seller-product-activate",
    ),
    path(
        "products/<uuid:id>/",
        SellerProductDetailAPIView.as_view(),
        name="seller-product-detail",
    ),
]