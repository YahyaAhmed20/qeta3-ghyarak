from django.urls import path

from apps.catalog.api.views import (
    ProductCompatibilityDetailAPIView,
    ProductCompatibilityListAPIView,
    ProductDetailAPIView,
    ProductListAPIView,
    ProductPartNumberDetailAPIView,
    ProductPartNumberListCreateAPIView,
)

app_name = "catalog"

urlpatterns = [
    path(
        "products/",
        ProductListAPIView.as_view(),
        name="product-list",
    ),
    path(
        "products/<uuid:id>/",
        ProductDetailAPIView.as_view(),
        name="product-detail",
    ),
    path(
        "part-numbers/",
        ProductPartNumberListCreateAPIView.as_view(),
        name="part-number-list-create",
    ),

    path(
        "part-numbers/<uuid:id>/",
        ProductPartNumberDetailAPIView.as_view(),
        name="part-number-detail",
    ),
    path(
        "products/<uuid:product_id>/compatibilities/",
        ProductCompatibilityListAPIView.as_view(),
        name="product-compatibility-list",
    ),
    path(
        "compatibilities/<uuid:id>/",
        ProductCompatibilityDetailAPIView.as_view(),
        name="compatibility-detail",
    ),
]