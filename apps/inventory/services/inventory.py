from django.db import transaction

from apps.inventory.constants import InventoryMovementType
from apps.inventory.models import Inventory, InventoryMovement


class InventoryService:

    @staticmethod
    @transaction.atomic
    def restock(*, inventory_id, quantity, user=None, note=""):
        if quantity <= 0:
            raise ValueError("Restock quantity must be greater than zero.")

        inventory = (
            Inventory.objects
            .select_for_update()
            .get(id=inventory_id)
        )

        inventory.on_hand += quantity
        inventory.save(
            update_fields=["on_hand", "updated_at"]
        )

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.RESTOCK,
            quantity=quantity,
            note=note,
            created_by=user,
        )

        return inventory

    @staticmethod
    @transaction.atomic
    def reserve(*, inventory_id, quantity, user=None, note=""):
        if quantity <= 0:
            raise ValueError(
                "Reservation quantity must be greater than zero."
            )

        inventory = (
            Inventory.objects
            .select_for_update()
            .get(id=inventory_id)
        )

        available = inventory.on_hand - inventory.reserved

        if quantity > available:
            raise ValueError("Insufficient available stock.")

        inventory.reserved += quantity
        inventory.save(
            update_fields=["reserved", "updated_at"]
        )

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.RESERVATION,
            quantity=quantity,
            note=note,
            created_by=user,
        )

        return inventory

    @staticmethod
    @transaction.atomic
    def release(*, inventory_id, quantity, user=None, note=""):
        if quantity <= 0:
            raise ValueError(
                "Release quantity must be greater than zero."
            )

        inventory = (
            Inventory.objects
            .select_for_update()
            .get(id=inventory_id)
        )

        if quantity > inventory.reserved:
            raise ValueError(
                "Release quantity cannot exceed reserved stock."
            )

        inventory.reserved -= quantity
        inventory.save(
            update_fields=["reserved", "updated_at"]
        )

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.RELEASE,
            quantity=quantity,
            note=note,
            created_by=user,
        )

        return inventory

    @staticmethod
    @transaction.atomic
    def sell(*, inventory_id, quantity, user=None, note=""):
        if quantity <= 0:
            raise ValueError(
                "Sale quantity must be greater than zero."
            )

        inventory = (
            Inventory.objects
            .select_for_update()
            .get(id=inventory_id)
        )

        if quantity > inventory.reserved:
            raise ValueError(
                "Sale quantity cannot exceed reserved stock."
            )

        inventory.on_hand -= quantity
        inventory.reserved -= quantity

        inventory.save(
            update_fields=[
                "on_hand",
                "reserved",
                "updated_at",
            ]
        )

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.SALE,
            quantity=quantity,
            note=note,
            created_by=user,
        )

        return inventory

    @staticmethod
    @transaction.atomic
    def return_stock(*, inventory_id, quantity, user=None, note=""):
        if quantity <= 0:
            raise ValueError(
                "Return quantity must be greater than zero."
            )

        inventory = (
            Inventory.objects
            .select_for_update()
            .get(id=inventory_id)
        )

        inventory.on_hand += quantity

        inventory.save(
            update_fields=["on_hand", "updated_at"]
        )

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.RETURN,
            quantity=quantity,
            note=note,
            created_by=user,
        )

        return inventory

    @staticmethod
    @transaction.atomic
    def adjust(
        *,
        inventory_id,
        quantity,
        user=None,
        note="",
    ):
        if quantity == 0:
            raise ValueError(
                "Adjustment quantity cannot be zero."
            )

        inventory = (
            Inventory.objects
            .select_for_update()
            .get(id=inventory_id)
        )

        new_on_hand = inventory.on_hand + quantity

        if new_on_hand < 0:
            raise ValueError(
                "Adjustment cannot make on-hand stock negative."
            )

        if new_on_hand < inventory.reserved:
            raise ValueError(
                "Adjustment would make reserved stock exceed on-hand stock."
            )

        inventory.on_hand = new_on_hand

        inventory.save(
            update_fields=["on_hand", "updated_at"]
        )

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.ADJUSTMENT,
            quantity=abs(quantity),
            note=note,
            created_by=user,
        )

        return inventory