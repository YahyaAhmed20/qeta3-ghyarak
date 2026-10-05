from django.urls import path

from apps.inventory.api.views import (
    SellerInventoryListAPIView,
    SellerInventoryRestockAPIView,
    SellerInventoryMovementsAPIView,
)


urlpatterns = [
    path(
        "",
        SellerInventoryListAPIView.as_view(),
        name="seller-inventory-list",
    ),
    path(
        "<uuid:inventory_id>/restock/",
        SellerInventoryRestockAPIView.as_view(),
        name="seller-inventory-restock",
    ),
    
    path(
    "<uuid:inventory_id>/movements/",
    SellerInventoryMovementsAPIView.as_view(),
    name="seller-inventory-movements",
),
]