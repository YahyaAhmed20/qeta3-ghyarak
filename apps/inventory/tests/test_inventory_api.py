import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.inventory.models import Inventory
from apps.stores.models import SellerProduct, Store, StoreStatus


@pytest.mark.django_db
class TestSellerInventoryAPI:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def seller_owner(self):
        return User.objects.create_user(
            phone="+201009999999",
            role="SELLER_OWNER",
        )

    @pytest.fixture
    def active_store(self, seller_owner):
        return Store.objects.create(
            owner=seller_owner,
            name="Inventory Test Store",
            slug="inventory-test-store",
            phone="+201009999999",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

    @pytest.fixture
    def category(self):
        return Category.objects.create(
            name="Filters",
            slug="inventory-filters",
        )

    @pytest.fixture
    def brand(self):
        return Brand.objects.create(
            name="Bosch",
            slug="inventory-bosch",
        )

    @pytest.fixture
    def active_product(self, category, brand):
        return Product.objects.create(
            category=category,
            brand=brand,
            name="Bosch Oil Filter",
            slug="inventory-bosch-oil-filter",
            product_type="AFTERMARKET",
            is_active=True,
        )

    @pytest.fixture
    def seller_product(
        self,
        active_store,
        active_product,
    ):
        return SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            seller_sku="BOSCH-INV-001",
            price="450.00",
            sale_price="400.00",
            is_active=True,
        )

    @pytest.fixture
    def inventory(self, seller_product):
        return Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=3,
        )

    def test_list_own_inventory(
        self,
        client,
        seller_owner,
        active_store,
        inventory,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.get(
            "/api/v1/inventory/",
        )

        assert response.status_code == 200
        assert len(response.data) == 1

        item = response.data[0]

        assert item["id"] == str(inventory.id)
        assert item["product_name"] == "Bosch Oil Filter"
        assert item["brand_name"] == "Bosch"
        assert item["category_name"] == "Filters"
        assert item["seller_sku"] == "BOSCH-INV-001"

        assert item["price"] == "450.00"
        assert item["sale_price"] == "400.00"

        assert item["on_hand"] == 10
        assert item["reserved"] == 3
        assert item["available_stock"] == 7

        assert item["is_active"] is True

    def test_inventory_requires_authentication(
        self,
        client,
    ):
        response = client.get(
            "/api/v1/inventory/",
        )

        assert response.status_code == 401

    def test_inventory_does_not_include_other_store(
        self,
        client,
        seller_owner,
        active_store,
        inventory,
    ):
        other_owner = User.objects.create_user(
            phone="+201009999998",
            role="SELLER_OWNER",
        )

        other_store = Store.objects.create(
            owner=other_owner,
            name="Other Inventory Store",
            slug="other-inventory-store",
            phone="+201009999998",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        other_category = Category.objects.create(
            name="Brakes",
            slug="inventory-brakes",
        )

        other_brand = Brand.objects.create(
            name="TRW",
            slug="inventory-trw",
        )

        other_product = Product.objects.create(
            category=other_category,
            brand=other_brand,
            name="TRW Brake Pads",
            slug="inventory-trw-brake-pads",
            product_type="AFTERMARKET",
            is_active=True,
        )

        other_seller_product = SellerProduct.objects.create(
            store=other_store,
            product=other_product,
            seller_sku="TRW-INV-001",
            price="1200.00",
            sale_price="1100.00",
            is_active=True,
        )

        Inventory.objects.create(
            seller_product=other_seller_product,
            on_hand=20,
            reserved=5,
        )

        client.force_authenticate(user=seller_owner)

        response = client.get(
            "/api/v1/inventory/",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(inventory.id)

    def test_restock_inventory_success(
        self,
        client,
        seller_owner,
        inventory,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.post(
            f"/api/v1/inventory/{inventory.id}/restock/",
            {
                "quantity": 5,
                "note": "New stock received",
            },
            format="json",
        )

        assert response.status_code == 200

        inventory.refresh_from_db()

        assert inventory.on_hand == 15
        assert inventory.reserved == 3
        assert inventory.available == 12

        assert response.data["on_hand"] == 15
        assert response.data["reserved"] == 3
        assert response.data["available_stock"] == 12

        from apps.inventory.constants import InventoryMovementType
        from apps.inventory.models import InventoryMovement

        movement = InventoryMovement.objects.get(
            inventory=inventory,
            movement_type=InventoryMovementType.RESTOCK,
            quantity=5,
        )

        assert movement.note == "New stock received"
        assert movement.created_by == seller_owner

    def test_restock_cannot_access_other_store_inventory(
        self,
        client,
        seller_owner,
        inventory,
    ):
        other_owner = User.objects.create_user(
            phone="+201009999997",
            role="SELLER_OWNER",
        )

        client.force_authenticate(user=other_owner)

        response = client.post(
            f"/api/v1/inventory/{inventory.id}/restock/",
            {
                "quantity": 5,
            },
            format="json",
        )

        assert response.status_code == 400

        inventory.refresh_from_db()

        assert inventory.on_hand == 10
        assert inventory.reserved == 3

    def test_restock_cannot_modify_inventory_of_another_store(
        self,
        client,
        seller_owner,
        inventory,
    ):
        other_owner = User.objects.create_user(
            phone="+201009999996",
            role="SELLER_OWNER",
        )

        Store.objects.create(
            owner=other_owner,
            name="Other Store",
            slug="other-store-restock",
            phone="+201009999996",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        client.force_authenticate(user=other_owner)

        response = client.post(
            f"/api/v1/inventory/{inventory.id}/restock/",
            {
                "quantity": 5,
            },
            format="json",
        )

        assert response.status_code == 404

        inventory.refresh_from_db()

        assert inventory.on_hand == 10
        assert inventory.reserved == 3

    def test_list_inventory_movements(
        self,
        client,
        seller_owner,
        inventory,
    ):
        from apps.inventory.models import InventoryMovement

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type="RESTOCK",
            quantity=5,
            note="Initial restock",
            created_by=seller_owner,
        )

        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type="SALE",
            quantity=2,
            note="Customer order",
            created_by=seller_owner,
        )

        client.force_authenticate(user=seller_owner)

        response = client.get(
            f"/api/v1/inventory/{inventory.id}/movements/"
        )

        assert response.status_code == 200
        assert len(response.data) == 2

        movements = {
            item["movement_type"]: item
            for item in response.data
        }

        assert movements["SALE"]["movement_type_label"] == "Sale"
        assert movements["SALE"]["quantity"] == 2
        assert movements["SALE"]["note"] == "Customer order"

        assert movements["RESTOCK"]["movement_type_label"] == "Restock"
        assert movements["RESTOCK"]["quantity"] == 5
        assert movements["RESTOCK"]["note"] == "Initial restock"

    def test_inventory_movements_requires_authentication(
        self,
        client,
        inventory,
    ):
        response = client.get(
            f"/api/v1/inventory/{inventory.id}/movements/"
        )

        assert response.status_code == 401

    def test_inventory_movements_cannot_access_other_store(
        self,
        client,
        inventory,
    ):
        other_owner = User.objects.create_user(
            phone="+201001111111",
            password="testpass123",
            role="SELLER_OWNER",
        )

        Store.objects.create(
            owner=other_owner,
            name="Other Inventory Store",
            slug="other-inventory-store",
            phone="+201001111111",
            address="Other Address",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        client.force_authenticate(user=other_owner)

        response = client.get(
            f"/api/v1/inventory/{inventory.id}/movements/"
        )

        assert response.status_code == 200
        assert response.data == []
        
    def test_inventory_movements_not_found_for_unknown_inventory(
        self,
        client,
        seller_owner,
    ):
        import uuid

        client.force_authenticate(user=seller_owner)

        response = client.get(
            f"/api/v1/inventory/{uuid.uuid4()}/movements/"
        )

        assert response.status_code == 200
        assert response.data == []