from django.urls import path

from apps.orders.api.views import SellerOrderListAPIView
from apps.orders.api.views import (
    SellerOrderAcceptAPIView,
    SellerOrderDetailAPIView,
    SellerOrderListAPIView,
    SellerOrderPreparingAPIView,
    SellerOrderReadyAPIView,
    SellerOrderOutForDeliveryAPIView,
)


urlpatterns = [
    path(
        "orders/",
        SellerOrderListAPIView.as_view(),
        name="seller-order-list",
    ),
    path(
    "orders/<uuid:order_id>/",
    SellerOrderDetailAPIView.as_view(),
    name="seller-order-detail",
),
    
    path(
    "orders/<uuid:order_id>/accept/",
    SellerOrderAcceptAPIView.as_view(),
    name="seller-order-accept",
),
    path(
    "orders/<uuid:order_id>/preparing/",
    SellerOrderPreparingAPIView.as_view(),
    name="seller-order-preparing",
),
    path(
    "orders/<uuid:order_id>/ready/",
    SellerOrderReadyAPIView.as_view(),
    name="seller-order-ready",
),
    
    path(
    "orders/<uuid:order_id>/out-for-delivery/",
    SellerOrderOutForDeliveryAPIView.as_view(),
    name="seller-order-out-for-delivery",
),
]
