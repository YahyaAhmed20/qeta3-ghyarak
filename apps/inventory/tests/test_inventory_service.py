import pytest

from apps.inventory.constants import InventoryMovementType
from apps.inventory.models import InventoryMovement
from apps.inventory.services.inventory import InventoryService


@pytest.mark.django_db
class TestInventoryService:

    def test_restock_increases_on_hand(self, inventory):
        result = InventoryService.restock(
            inventory_id=inventory.id,
            quantity=5,
        )

        assert result.on_hand == 15
        assert result.reserved == 2
        assert result.available == 13

    def test_restock_creates_movement(self, inventory):
        InventoryService.restock(
            inventory_id=inventory.id,
            quantity=5,
            note="New stock",
        )

        movement = InventoryMovement.objects.get(
            inventory=inventory,
            movement_type=InventoryMovementType.RESTOCK,
        )

        assert movement.quantity == 5
        assert movement.note == "New stock"

    def test_restock_rejects_zero(self, inventory):
        with pytest.raises(ValueError):
            InventoryService.restock(
                inventory_id=inventory.id,
                quantity=0,
            )

    def test_reserve_increases_reserved(self, inventory):
        result = InventoryService.reserve(
            inventory_id=inventory.id,
            quantity=3,
        )

        assert result.on_hand == 10
        assert result.reserved == 5
        assert result.available == 5

    def test_reserve_creates_movement(self, inventory):
        InventoryService.reserve(
            inventory_id=inventory.id,
            quantity=3,
        )

        movement = InventoryMovement.objects.get(
            inventory=inventory,
            movement_type=InventoryMovementType.RESERVATION,
        )

        assert movement.quantity == 3

    def test_reserve_rejects_insufficient_stock(self, inventory):
        with pytest.raises(ValueError, match="Insufficient available stock."):
            InventoryService.reserve(
                inventory_id=inventory.id,
                quantity=9,
            )

        inventory.refresh_from_db()

        assert inventory.on_hand == 10
        assert inventory.reserved == 2
        assert inventory.available == 8

        assert not InventoryMovement.objects.filter(
            inventory=inventory,
            movement_type=InventoryMovementType.RESERVATION,
        ).exists()

    def test_release_decreases_reserved(self, inventory):
        result = InventoryService.release(
            inventory_id=inventory.id,
            quantity=1,
        )

        assert result.on_hand == 10
        assert result.reserved == 1
        assert result.available == 9

    def test_release_creates_movement(self, inventory):
        InventoryService.release(
            inventory_id=inventory.id,
            quantity=1,
        )

        movement = InventoryMovement.objects.get(
            inventory=inventory,
            movement_type=InventoryMovementType.RELEASE,
        )

        assert movement.quantity == 1

    def test_release_cannot_exceed_reserved(self, inventory):
        with pytest.raises(
            ValueError,
            match="Release quantity cannot exceed reserved stock.",
        ):
            InventoryService.release(
                inventory_id=inventory.id,
                quantity=3,
            )

    def test_sell_decreases_on_hand_and_reserved(self, inventory):
        result = InventoryService.sell(
            inventory_id=inventory.id,
            quantity=2,
        )

        assert result.on_hand == 8
        assert result.reserved == 0
        assert result.available == 8

    def test_sell_creates_movement(self, inventory):
        InventoryService.sell(
            inventory_id=inventory.id,
            quantity=2,
        )

        movement = InventoryMovement.objects.get(
            inventory=inventory,
            movement_type=InventoryMovementType.SALE,
        )

        assert movement.quantity == 2

    def test_sell_cannot_exceed_reserved(self, inventory):
        with pytest.raises(
            ValueError,
            match="Sale quantity cannot exceed reserved stock.",
        ):
            InventoryService.sell(
                inventory_id=inventory.id,
                quantity=3,
            )

    def test_return_stock_increases_on_hand(self, inventory):
        result = InventoryService.return_stock(
            inventory_id=inventory.id,
            quantity=3,
        )

        assert result.on_hand == 13
        assert result.reserved == 2
        assert result.available == 11

    def test_return_stock_creates_movement(self, inventory):
        InventoryService.return_stock(
            inventory_id=inventory.id,
            quantity=3,
        )

        movement = InventoryMovement.objects.get(
            inventory=inventory,
            movement_type=InventoryMovementType.RETURN,
        )

        assert movement.quantity == 3

    def test_adjust_positive_quantity(self, inventory):
        result = InventoryService.adjust(
            inventory_id=inventory.id,
            quantity=5,
        )

        assert result.on_hand == 15
        assert result.reserved == 2
        assert result.available == 13

    def test_adjust_negative_quantity(self, inventory):
        result = InventoryService.adjust(
            inventory_id=inventory.id,
            quantity=-3,
        )

        assert result.on_hand == 7
        assert result.reserved == 2
        assert result.available == 5

    def test_adjust_cannot_make_on_hand_negative(self, inventory):
        with pytest.raises(
            ValueError,
            match="Adjustment cannot make on-hand stock negative.",
        ):
            InventoryService.adjust(
                inventory_id=inventory.id,
                quantity=-11,
            )

    def test_adjust_cannot_reduce_below_reserved(self, inventory):
        with pytest.raises(
            ValueError,
            match="Adjustment would make reserved stock exceed on-hand stock.",
        ):
            InventoryService.adjust(
                inventory_id=inventory.id,
                quantity=-9,
            )