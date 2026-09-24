import pytest

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.stores.models import Store, StoreStatus, SellerProduct


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
        slug="alfa-spare-parts-cart",
        phone="+201001234569",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )


@pytest.fixture
def inactive_store(seller_owner):
    return Store.objects.create(
        owner=seller_owner,
        name="Inactive Store",
        slug="inactive-store-cart",
        phone="+201001234569",
        address="Suez",
        city="Suez",
        status=StoreStatus.SUSPENDED,
        is_verified=True,
    )


@pytest.fixture
def unverified_store(seller_owner):
    return Store.objects.create(
        owner=seller_owner,
        name="Unverified Store",
        slug="unverified-store-cart",
        phone="+201001234569",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=False,
    )


@pytest.fixture
def active_product(db):
    category = Category.objects.create(
        name="Filters",
        slug="filters-cart",
    )

    brand = Brand.objects.create(
        name="Bosch",
        slug="bosch-cart",
    )

    return Product.objects.create(
        category=category,
        brand=brand,
        name="Bosch Oil Filter",
        slug="bosch-oil-filter-cart",
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
def cart(customer, active_store):
    from apps.cart.models import Cart

    return Cart.objects.create(
        customer=customer,
        store=active_store,
    )