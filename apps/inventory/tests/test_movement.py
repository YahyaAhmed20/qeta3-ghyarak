import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.inventory.constants import InventoryMovementType
from apps.inventory.models import Inventory, InventoryMovement
from apps.stores.models import SellerProduct, Store, StoreStatus


@pytest.fixture
def seller_owner(db):
    return User.objects.create_user(
        phone="+201001234567",
        role="SELLER_OWNER",
    )


@pytest.fixture
def active_store(seller_owner):
    return Store.objects.create(
        owner=seller_owner,
        name="Alfa Spare Parts",
        slug="alfa-spare-parts",
        phone="+201001234567",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )


@pytest.fixture
def active_product(db):
    category = Category.objects.create(
        name="Filters",
        slug="filters",
    )

    brand = Brand.objects.create(
        name="Bosch",
        slug="bosch",
    )

    return Product.objects.create(
        category=category,
        brand=brand,
        name="Bosch Oil Filter",
        slug="bosch-oil-filter",
        product_type="AFTERMARKET",
        is_active=True,
    )


@pytest.fixture
def inventory(active_store, active_product):
    seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )

    return Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=2,
    )


@pytest.mark.django_db
class TestInventoryMovementModel:

    def test_create_movement(self, inventory):
        movement = InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.RESTOCK,
            quantity=10,
            note="Initial stock",
        )

        assert movement.inventory == inventory
        assert movement.movement_type == InventoryMovementType.RESTOCK
        assert movement.quantity == 10
        assert movement.note == "Initial stock"

    def test_all_movement_types_are_supported(self, inventory):
        for movement_type in InventoryMovementType.values:
            movement = InventoryMovement.objects.create(
                inventory=inventory,
                movement_type=movement_type,
                quantity=1,
            )

            assert movement.movement_type == movement_type

    def test_quantity_must_be_positive(self, inventory):
        movement = InventoryMovement(
            inventory=inventory,
            movement_type=InventoryMovementType.RESTOCK,
            quantity=0,
        )

        with pytest.raises(ValidationError):
            movement.full_clean()

    def test_negative_quantity_is_rejected(self, inventory):
        movement = InventoryMovement(
            inventory=inventory,
            movement_type=InventoryMovementType.SALE,
            quantity=-1,
        )

        with pytest.raises(ValidationError):
            movement.full_clean()

    def test_reference_fields_are_optional(self, inventory):
        movement = InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.ADJUSTMENT,
            quantity=2,
        )

        assert movement.reference_type == ""
        assert movement.reference_id == ""
        assert movement.note == ""
        assert movement.created_by is None

    def test_created_by_is_saved(self, inventory, seller_owner):
        movement = InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=InventoryMovementType.ADJUSTMENT,
            quantity=2,
            created_by=seller_owner,
        )

        assert movement.created_by == seller_owner