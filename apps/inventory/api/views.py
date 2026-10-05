from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.api.serializers import (
    SellerInventorySerializer,
    InventoryRestockSerializer,
    InventoryMovementSerializer,
)
from apps.inventory.models import Inventory, InventoryMovement
from apps.inventory.services.inventory import InventoryService
from apps.inventory.selectors.inventory import InventorySelector
from apps.stores.models import Store


class SellerInventoryListAPIView(ListAPIView):
    serializer_class = SellerInventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        store = (
            Store.objects
            .filter(
                owner=self.request.user,
                status="ACTIVE",
                is_verified=True,
            )
            .first()
        )

        if not store:
            return Inventory.objects.none()

        return InventorySelector.get_store_inventory(store)


class SellerInventoryRestockAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, inventory_id):
        store = (
            Store.objects
            .filter(
                owner=request.user,
                status="ACTIVE",
                is_verified=True,
            )
            .first()
        )

        if not store:
            return Response(
                {
                    "detail": "You do not have an active verified store."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        inventory = InventorySelector.get_store_inventory_item(
            store=store,
            inventory_id=inventory_id,
        )

        if inventory is None:
            return Response(
                {
                    "detail": "Inventory not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InventoryRestockSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        try:
            inventory = InventoryService.restock(
                inventory_id=inventory.id,
                quantity=serializer.validated_data["quantity"],
                user=request.user,
                note=serializer.validated_data.get("note", ""),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            SellerInventorySerializer(inventory).data,
            status=status.HTTP_200_OK,
        )


class SellerInventoryMovementsAPIView(ListAPIView):
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        store = Store.objects.filter(
            owner=self.request.user,
            status="ACTIVE",
            is_verified=True,
        ).first()

        if not store:
            return InventoryMovement.objects.none()

        inventory_id = self.kwargs["inventory_id"]

        inventory = InventorySelector.get_store_inventory_item(
            store=store,
            inventory_id=inventory_id,
        )

        if inventory is None:
            return InventoryMovement.objects.none()

        return InventorySelector.get_store_inventory_movements(
            store=store,
            inventory_id=inventory_id,
        )