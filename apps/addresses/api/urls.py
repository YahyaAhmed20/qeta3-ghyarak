from django.urls import path

from apps.addresses.api.views import (
    AddressDetailAPIView,
    AddressListCreateAPIView,
)


urlpatterns = [
    path(
        "",
        AddressListCreateAPIView.as_view(),
        name="address-list-create",
    ),
    path(
        "<uuid:address_id>/",
        AddressDetailAPIView.as_view(),
        name="address-detail",
    ),
]