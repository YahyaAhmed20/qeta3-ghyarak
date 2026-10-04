from django.urls import path

from apps.vehicles.api.catalog_views import (
    VehicleEngineListAPIView,
    VehicleGenerationListAPIView,
    VehicleMakeListAPIView,
    VehicleModelListAPIView,
    VehicleVariantListAPIView,
)
from apps.vehicles.api.views import (
    CustomerVehicleDetailAPIView,
    CustomerVehicleListCreateAPIView,
    CustomerVehicleSetDefaultAPIView,
)


urlpatterns = [
    # Vehicle Catalog
    path(
        "catalog/makes/",
        VehicleMakeListAPIView.as_view(),
        name="vehicle-catalog-makes",
    ),
    path(
        "catalog/makes/<uuid:make_id>/models/",
        VehicleModelListAPIView.as_view(),
        name="vehicle-catalog-models",
    ),
    path(
        "catalog/models/<uuid:model_id>/generations/",
        VehicleGenerationListAPIView.as_view(),
        name="vehicle-catalog-generations",
    ),
    path(
        "catalog/generations/<uuid:generation_id>/engines/",
        VehicleEngineListAPIView.as_view(),
        name="vehicle-catalog-engines",
    ),
    path(
        "catalog/engines/<uuid:engine_id>/variants/",
        VehicleVariantListAPIView.as_view(),
        name="vehicle-catalog-variants",
    ),

    # Customer Garage
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