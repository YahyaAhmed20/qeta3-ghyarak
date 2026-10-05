from apps.inventory.models import (
    Inventory,
    InventoryMovement,
)


class InventorySelector:

    @staticmethod
    def get_store_inventory(store):
        return (
            Inventory.objects
            .select_related(
                "seller_product",
                "seller_product__product",
                "seller_product__product__brand",
                "seller_product__product__category",
            )
            .filter(
                seller_product__store=store,
            )
            .order_by(
                "seller_product__product__name"
            )
        )

    @staticmethod
    def get_store_inventory_item(*, store, inventory_id):
        return (
            Inventory.objects
            .select_related(
                "seller_product",
                "seller_product__product",
                "seller_product__product__brand",
                "seller_product__product__category",
            )
            .filter(
                id=inventory_id,
                seller_product__store=store,
            )
            .first()
        )

    @staticmethod
    def get_store_inventory_movements(
        *,
        store,
        inventory_id,
    ):
        return (
            InventoryMovement.objects
            .select_related(
                "inventory",
                "inventory__seller_product",
                "inventory__seller_product__product",
                "created_by",
            )
            .filter(
                inventory_id=inventory_id,
                inventory__seller_product__store=store,
            )
            .order_by("-created_at")
        )