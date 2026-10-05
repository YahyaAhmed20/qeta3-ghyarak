from decimal import Decimal
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.finance.models.settlement import (
    Settlement,
    SettlementStatus,
)
from apps.inventory.models.inventory import Inventory
from apps.orders.models.order import (
    Order,
    OrderStatus,
)
from apps.stores.models import Store, StoreStatus
from apps.stores.models.seller_product import SellerProduct

from apps.dashboard.selectors.overview import (
    DashboardOverviewSelector,
)


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
def customer():
    return User.objects.create_user(
        phone="+201009876543",
        role="CUSTOMER",
    )


@pytest.fixture
def seller_product(active_store, active_product):
    return SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        seller_sku="BOSCH-OF-001",
        price=Decimal("250.00"),
        sale_price=Decimal("230.00"),
        is_active=True,
    )


@pytest.fixture
def inventory(seller_product):
    return Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=2,
    )


@pytest.fixture
def delivered_order(active_store, customer):
    return Order.objects.create(
        customer=customer,
        store=active_store,
        status=OrderStatus.DELIVERED,
        subtotal=Decimal("250.00"),
        seller_discount=Decimal("20.00"),
        platform_discount=Decimal("0.00"),
        delivery_fee=Decimal("50.00"),
        total=Decimal("280.00"),
        address_snapshot={},
    )


@pytest.mark.django_db
def test_overview_returns_store_info(active_store):
    data = DashboardOverviewSelector.get_overview(
        active_store
    )

    assert data["store"]["id"] == active_store.id
    assert data["store"]["name"] == "Alfa Spare Parts"
    assert data["store"]["status"] == "ACTIVE"
    assert data["store"]["is_verified"] is True


@pytest.mark.django_db
def test_overview_counts_inventory(
    active_store,
    seller_product,
    inventory,
):
    inventory.on_hand = 0
    inventory.reserved = 0
    inventory.save(update_fields=["on_hand", "reserved"])

    data = DashboardOverviewSelector.get_overview(
        active_store
    )

    assert data["inventory"]["total_products"] == 1
    assert data["inventory"]["out_of_stock"] == 1


@pytest.mark.django_db
def test_overview_counts_delivered_sales(
    active_store,
    delivered_order,
):
    data = DashboardOverviewSelector.get_overview(
        active_store
    )

    assert data["orders"]["total"] == 1
    assert data["orders"]["delivered"] == 1
    assert data["sales"]["total"] == Decimal("230.00")


@pytest.mark.django_db
def test_overview_counts_settlements(active_store):
    Settlement.objects.create(
        store=active_store,
        period_start=timezone.localdate() - timedelta(days=7),
        period_end=timezone.localdate(),
        net_amount=Decimal("1000.00"),
        status=SettlementStatus.PENDING,
    )

    Settlement.objects.create(
        store=active_store,
        period_start=timezone.localdate() - timedelta(days=14),
        period_end=timezone.localdate() - timedelta(days=7),
        net_amount=Decimal("2000.00"),
        status=SettlementStatus.PAID,
        payment_reference="PAY-001",
        paid_at=timezone.now(),
    )

    data = DashboardOverviewSelector.get_overview(
        active_store
    )

    assert data["settlements"]["pending"] == Decimal("1000.00")
    assert data["settlements"]["paid"] == Decimal("2000.00")
    assert data["settlements"]["ready"] == Decimal("0.00")
    assert data["settlements"]["processing"] == Decimal("0.00")
    
    
@pytest.fixture
def second_store():
    owner = User.objects.create_user(
        phone="+201002222222",
        role="SELLER_OWNER",
    )

    return Store.objects.create(
        owner=owner,
        name="Beta Spare Parts",
        slug="beta-spare-parts",
        phone="+201002222222",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )


@pytest.mark.django_db
def test_overview_isolated_by_store(
    active_store,
    second_store,
    customer,
    active_product,
):
    SellerProduct.objects.create(
        store=second_store,
        product=active_product,
        seller_sku="BETA-001",
        price=Decimal("500.00"),
        is_active=True,
    )

    Inventory.objects.create(
        seller_product=second_store.seller_products.get(),
        on_hand=20,
        reserved=0,
    )

    Order.objects.create(
        customer=customer,
        store=second_store,
        status=OrderStatus.DELIVERED,
        subtotal=Decimal("500.00"),
        seller_discount=Decimal("0.00"),
        platform_discount=Decimal("0.00"),
        delivery_fee=Decimal("50.00"),
        total=Decimal("550.00"),
        address_snapshot={},
    )

    Settlement.objects.create(
        store=second_store,
        period_start=timezone.localdate() - timedelta(days=7),
        period_end=timezone.localdate(),
        net_amount=Decimal("400.00"),
        status=SettlementStatus.PENDING,
    )

    data = DashboardOverviewSelector.get_overview(
        active_store
    )

    assert data["orders"]["total"] == 0
    assert data["orders"]["delivered"] == 0

    assert data["sales"]["total"] == Decimal("0.00")

    assert data["inventory"]["total_products"] == 0
    assert data["inventory"]["out_of_stock"] == 0

    assert data["settlements"]["pending"] == Decimal("0.00")