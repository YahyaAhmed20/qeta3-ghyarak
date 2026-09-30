from decimal import Decimal

import pytest

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.orders.models import Order, OrderItem
from apps.stores.models import Store
from apps.stores.models.seller_product import SellerProduct


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        phone="+201001234581",
        role="CUSTOMER",
        is_active=True,
    )


@pytest.fixture
def another_customer(db):
    return User.objects.create_user(
        phone="+201001234592",
        role="CUSTOMER",
        is_active=True,
    )


@pytest.fixture
def finance_owner(db):
    return User.objects.create_user(
        phone="+201001234580",
        role="SELLER_OWNER",
        is_active=True,
    )


@pytest.fixture
def active_store(finance_owner):
    return Store.objects.create(
        owner=finance_owner,
        name="Review Test Store",
        slug="review-test-store",
        phone="+201001234580",
        address="Test Address",
        city="Suez",
        status="ACTIVE",
        is_verified=True,
    )


@pytest.fixture
def active_product(db):
    category = Category.objects.create(
        name="Filters",
        slug="filters-reviews",
    )

    brand = Brand.objects.create(
        name="Bosch",
        slug="bosch-reviews",
    )

    return Product.objects.create(
        category=category,
        brand=brand,
        name="Bosch Oil Filter",
        slug="bosch-oil-filter-reviews",
        product_type="AFTERMARKET",
        is_active=True,
    )


@pytest.fixture
def seller_product(active_store, active_product):
    return SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price=Decimal("250.00"),
        is_active=True,
    )


@pytest.fixture
def order(customer, active_store):
    return Order.objects.create(
        customer=customer,
        store=active_store,
        subtotal=Decimal("250.00"),
        seller_discount=Decimal("0.00"),
        platform_discount=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        total=Decimal("250.00"),
        address_snapshot={
            "city": "Suez",
            "address": "Test Address",
        },
    )


@pytest.fixture
def review_order_item(order, seller_product):
    return OrderItem.objects.create(
        order=order,
        seller_product=seller_product,
        product_name_snapshot=seller_product.product.name,
        part_number_snapshot="BOSCH-FILTER-001",
        unit_price=Decimal("250.00"),
        discount=Decimal("0.00"),
        quantity=1,
    )


@pytest.fixture
def another_store(db):
    another_owner = User.objects.create_user(
        phone="+201001234591",
        role="SELLER_OWNER",
        is_active=True,
    )

    return Store.objects.create(
        owner=another_owner,
        name="Another Review Store",
        slug="another-review-store",
        phone="+201001234591",
        address="Another Test Address",
        city="Suez",
        status="ACTIVE",
        is_verified=True,
    )