import pytest

from apps.catalog.models import Brand, Category, Product
from apps.inventory.models import Inventory
from apps.stores.models import SellerProduct, Store, StoreStatus
from apps.accounts.models import User


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