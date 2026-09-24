from decimal import Decimal

import pytest

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.stores.models import Store, StoreStatus


@pytest.fixture
def seller_owner():
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
def category():
    return Category.objects.create(
        name="Filters",
        slug="filters",
    )


@pytest.fixture
def brand():
    return Brand.objects.create(
        name="Bosch",
        slug="bosch",
    )


@pytest.fixture
def active_product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Bosch Oil Filter",
        slug="bosch-oil-filter",
        product_type="AFTERMARKET",
        is_active=True,
    )


@pytest.fixture
def inactive_product(category, brand):
    return Product.objects.create(
        category=category,
        brand=brand,
        name="Inactive Filter",
        slug="inactive-filter",
        product_type="AFTERMARKET",
        is_active=False,
    )