from django.urls import path

from apps.cart.api.views import (
    ActiveCartAPIView,
    CartItemCreateAPIView,
    CartItemUpdateAPIView,
    CartClearAPIView
)

urlpatterns = [
    path(
        "",
        ActiveCartAPIView.as_view(),
        name="active-cart",
    ),
    path(
        "items/",
        CartItemCreateAPIView.as_view(),
        name="cart-item-create",
    ),
    path(
        "items/<uuid:item_id>/",
        CartItemUpdateAPIView.as_view(),
        name="cart-item-update",
    ),
        path(
        "clear/",
        CartClearAPIView.as_view(),
        name="cart-clear",
    ),
]