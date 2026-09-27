from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.finance.models import CommissionRule
from apps.stores.models import Store
from apps.stores.models.seller_product import SellerProduct


@pytest.fixture
def finance_owner(db):
    return User.objects.create_user(
        phone="+201001234580",
        role="SELLER_OWNER",
        is_active=True,
    )


@pytest.fixture
def active_store(db, finance_owner):
    return Store.objects.create(
        owner=finance_owner,
        name="Finance Test Store",
        slug="finance-test-store",
        phone="+201001234580",
        address="Test Address",
        city="Suez",
        status="ACTIVE",
        is_verified=True,
    )


@pytest.fixture
def commission_rule(active_store):
    return CommissionRule.objects.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=timezone.now() - timedelta(minutes=1),
    )


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        phone="+201001234581",
        role="CUSTOMER",
        is_active=True,
    )


@pytest.fixture
def active_product(db):
    category = Category.objects.create(
        name="Filters",
        slug="filters-finance",
    )

    brand = Brand.objects.create(
        name="Bosch",
        slug="bosch-finance",
    )

    return Product.objects.create(
        category=category,
        brand=brand,
        name="Bosch Oil Filter",
        slug="bosch-oil-filter-finance",
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


@pytest.fixture
def delivery_user(db):
    return User.objects.create_user(
        phone="+201001234570",
        role="DELIVERY",
        is_active=True,
    )


@pytest.fixture
def finance_admin(db):
    return User.objects.create_user(
        phone="+201001234572",
        role="ADMIN",
        is_active=True,
    )