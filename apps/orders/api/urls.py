from django.urls import path

from apps.orders.api.views import (
    DeliveryAssignmentAcceptAPIView,
    DeliveryAssignmentCancelAPIView,
    DeliveryAssignmentCompleteAPIView,
    DeliveryAssignmentCreateAPIView,
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
]