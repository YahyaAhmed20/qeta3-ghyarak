from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.inventory.models.inventory import Inventory
from apps.stores.models import Store, StoreStatus
from apps.stores.models.seller_product import SellerProduct
from datetime import timedelta

from django.utils import timezone

from apps.finance.models.settlement import (
    Settlement,
    SettlementStatus,
)
from apps.orders.models.order import Order, OrderStatus

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seller_owner():
    return User.objects.create_user(
        phone="+201001234567",
        role="SELLER_OWNER",
    )


@pytest.fixture
def customer():
    return User.objects.create_user(
        phone="+201009876543",
        role="CUSTOMER",
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
def inactive_store(seller_owner):
    return Store.objects.create(
        owner=seller_owner,
        name="Inactive Spare Parts",
        slug="inactive-spare-parts",
        phone="+201001234567",
        address="Suez",
        city="Suez",
        status=StoreStatus.SUSPENDED,
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


@pytest.mark.django_db
def test_seller_owner_can_access_dashboard(
    api_client,
    seller_owner,
    active_store,
    seller_product,
    inventory,
):
    api_client.force_authenticate(user=seller_owner)

    response = api_client.get(
        "/api/v1/dashboard/overview/"
    )

    assert response.status_code == 200

    assert response.data["store"]["id"] == str(
        active_store.id
    )
    assert response.data["store"]["name"] == active_store.name

    assert response.data["orders"]["total"] == 0

    assert response.data["inventory"]["total_products"] == 1
    assert response.data["inventory"]["out_of_stock"] == 0

    assert response.data["sales"]["today"] == "0.00"
    assert response.data["sales"]["total"] == "0.00"


@pytest.mark.django_db
def test_customer_cannot_access_dashboard(
    api_client,
    customer,
):
    api_client.force_authenticate(user=customer)

    response = api_client.get(
        "/api/v1/dashboard/overview/"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_seller_owner_without_store_gets_404(
    api_client,
    seller_owner,
):
    api_client.force_authenticate(user=seller_owner)

    response = api_client.get(
        "/api/v1/dashboard/overview/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_suspended_store_gets_404(
    api_client,
    seller_owner,
    inactive_store,
):
    api_client.force_authenticate(user=seller_owner)

    response = api_client.get(
        "/api/v1/dashboard/overview/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_dashboard(
    api_client,
):
    response = api_client.get(
        "/api/v1/dashboard/overview/"
    )

    assert response.status_code == 401
    
@pytest.mark.django_db
def test_dashboard_returns_real_business_metrics(
    api_client,
    seller_owner,
    active_store,
    seller_product,
    inventory,
    customer,
):
    Order.objects.create(
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

    today = timezone.localdate()

    Settlement.objects.create(
        store=active_store,
        period_start=today - timedelta(days=7),
        period_end=today,
        net_amount=Decimal("1000.00"),
        status=SettlementStatus.PENDING,
    )

    Settlement.objects.create(
        store=active_store,
        period_start=today - timedelta(days=14),
        period_end=today - timedelta(days=7),
        net_amount=Decimal("2000.00"),
        status=SettlementStatus.PAID,
        payment_reference="PAY-001",
        paid_at=timezone.now(),
    )

    api_client.force_authenticate(user=seller_owner)

    response = api_client.get(
        "/api/v1/dashboard/overview/"
    )

    assert response.status_code == 200

    # Orders
    assert response.data["orders"]["total"] == 1
    assert response.data["orders"]["delivered"] == 1

    # Sales = subtotal - seller discount
    assert response.data["sales"]["today"] == "230.00"
    assert response.data["sales"]["total"] == "230.00"

    # Inventory
    assert response.data["inventory"]["total_products"] == 1
    assert response.data["inventory"]["out_of_stock"] == 0

    # Settlements
    assert response.data["settlements"]["pending"] == "1000.00"
    assert response.data["settlements"]["paid"] == "2000.00"
    assert response.data["settlements"]["ready"] == "0.00"
    assert response.data["settlements"]["processing"] == "0.00"
    
    
@pytest.mark.django_db
def test_dashboard_response_contract(
    api_client,
    seller_owner,
    active_store,
):
    api_client.force_authenticate(user=seller_owner)

    response = api_client.get(
        "/api/v1/dashboard/overview/"
    )

    assert response.status_code == 200

    assert set(response.data.keys()) == {
        "store",
        "orders",
        "sales",
        "inventory",
        "settlements",
    }

    assert set(response.data["store"].keys()) == {
        "id",
        "name",
        "status",
        "is_verified",
    }

    assert set(response.data["orders"].keys()) == {
        "total",
        "today",
        "pending",
        "delivered",
    }

    assert set(response.data["sales"].keys()) == {
        "today",
        "total",
    }

    assert set(response.data["inventory"].keys()) == {
        "total_products",
        "out_of_stock",
    }

    assert set(response.data["settlements"].keys()) == {
        "pending",
        "ready",
        "processing",
        "paid",
    }