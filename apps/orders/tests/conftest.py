import pytest

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.stores.models import Store
from apps.stores.models.seller_product import SellerProduct
from apps.stores.models.store import StoreStatus


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        phone="+201001234568",
        role="CUSTOMER",
    )


@pytest.fixture
def seller_owner(db):
    return User.objects.create_user(
        phone="+201001234569",
        role="SELLER_OWNER",
    )


@pytest.fixture
def active_store(seller_owner):
    return Store.objects.create(
        owner=seller_owner,
        name="Alfa Spare Parts",
        slug="alfa-spare-parts-orders",
        phone="+201001234569",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )


@pytest.fixture
def active_product(db):
    category = Category.objects.create(
        name="Filters",
        slug="filters-orders",
    )

    brand = Brand.objects.create(
        name="Bosch",
        slug="bosch-orders",
    )

    return Product.objects.create(
        category=category,
        brand=brand,
        name="Bosch Oil Filter",
        slug="bosch-oil-filter-orders",
        product_type="AFTERMARKET",
        is_active=True,
    )


@pytest.fixture
def seller_product(active_store, active_product):
    return SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
        is_active=True,
    )


@pytest.fixture
def order(customer, active_store):
    from apps.orders.models import Order

    return Order.objects.create(
        customer=customer,
        store=active_store,
        subtotal="250.00",
        seller_discount="0.00",
        platform_discount="0.00",
        delivery_fee="0.00",
        total="250.00",
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )