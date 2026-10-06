from django.urls import path

from apps.orders.api.views import (
    CheckoutAPIView,
    DeliveryAssignmentAcceptAPIView,
    DeliveryAssignmentCancelAPIView,
    DeliveryAssignmentCompleteAPIView,
    DeliveryAssignmentCreateAPIView,
    OrderListAPIView,
    OrderDetailAPIView,
)


urlpatterns = [
    path(
        "<uuid:order_id>/delivery/assign/",
        DeliveryAssignmentCreateAPIView.as_view(),
        name="delivery-assign",
    ),
    path(
        "delivery/assignments/<uuid:assignment_id>/accept/",
        DeliveryAssignmentAcceptAPIView.as_view(),
        name="delivery-assignment-accept",
    ),
    path(
        "delivery/assignments/<uuid:assignment_id>/cancel/",
        DeliveryAssignmentCancelAPIView.as_view(),
        name="delivery-assignment-cancel",
    ),
    path(
        "delivery/assignments/<uuid:assignment_id>/complete/",
        DeliveryAssignmentCompleteAPIView.as_view(),
        name="delivery-assignment-complete",
    ),
    path(
        "checkout/",
        CheckoutAPIView.as_view(),
        name="checkout",
    ),
    path(
        "",
        OrderListAPIView.as_view(),
        name="order-list",
    ),
    path(
        "<uuid:order_id>/",
        OrderDetailAPIView.as_view(),
        name="order-detail",
    ),
]