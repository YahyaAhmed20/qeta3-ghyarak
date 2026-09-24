import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.inventory.models import Inventory
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
def seller_product(active_store, active_product):
    return SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )


@pytest.mark.django_db
class TestInventoryModel:

    def test_create_inventory(self, seller_product):
        inventory = Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=3,
        )

        assert inventory.on_hand == 10
        assert inventory.reserved == 3
        assert inventory.available == 7

    def test_available_is_calculated(self, seller_product):
        inventory = Inventory.objects.create(
            seller_product=seller_product,
            on_hand=20,
            reserved=5,
        )

        assert inventory.available == 15

    def test_available_zero(self, seller_product):
        inventory = Inventory.objects.create(
            seller_product=seller_product,
            on_hand=5,
            reserved=5,
        )

        assert inventory.available == 0

    def test_reserved_cannot_exceed_on_hand(self, seller_product):
        inventory = Inventory(
            seller_product=seller_product,
            on_hand=5,
            reserved=6,
        )

        with pytest.raises(ValidationError):
            inventory.full_clean()

    def test_inventory_is_one_to_one_with_seller_product(
        self,
        seller_product,
    ):
        Inventory.objects.create(
            seller_product=seller_product,
        )

        with pytest.raises(IntegrityError):
            Inventory.objects.create(
                seller_product=seller_product,
            )