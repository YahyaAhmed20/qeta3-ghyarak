from django.urls import path

from apps.vehicles.api.views import (
    CustomerVehicleDetailAPIView,
    CustomerVehicleListCreateAPIView,
    CustomerVehicleSetDefaultAPIView,
)

urlpatterns = [
    path(
        "",
        CustomerVehicleListCreateAPIView.as_view(),
        name="customer-vehicle-list-create",
    ),
    path(
        "<uuid:vehicle_id>/",
        CustomerVehicleDetailAPIView.as_view(),
        name="customer-vehicle-detail",
    ),
    path(
        "<uuid:vehicle_id>/set-default/",
        CustomerVehicleSetDefaultAPIView.as_view(),
        name="customer-vehicle-set-default",
    ),
]