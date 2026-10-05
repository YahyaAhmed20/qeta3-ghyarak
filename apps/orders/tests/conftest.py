from datetime import timedelta
from decimal import Decimal
from apps.orders.models import DeliveryAssignment
from apps.orders.services.delivery_assignment import DeliveryAssignmentService
import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.finance.models import CommissionRule
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
def commission_rule(active_store):
    return CommissionRule.objects.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=timezone.now() - timedelta(minutes=1),
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
def order_item(order, seller_product):
    from apps.orders.models import OrderItem

    return OrderItem.objects.create(
        order=order,
        seller_product=seller_product,
        product_name_snapshot=seller_product.product.name,
        part_number_snapshot="BOSCH-OF-001",
        unit_price=Decimal("250.00"),
        discount=Decimal("0.00"),
        quantity=1,
    )
    
@pytest.fixture
def inventory(seller_product):
    from apps.inventory.models.inventory import Inventory

    return Inventory.objects.create(
        seller_product=seller_product,
        on_hand=1,
        reserved=1,
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
def delivery_assignment(order, delivery_user, seller_owner):
    order.status = "READY"
    order.save(update_fields=["status", "updated_at"])

    return DeliveryAssignmentService.assign(
        order_id=order.id,
        delivery_user=delivery_user,
        actor=seller_owner,
    )


@pytest.fixture
def delivery_user(db):
    return User.objects.create_user(
        phone="+201001234570",
        role="DELIVERY",
        is_active=True,
    )


@pytest.fixture
def another_delivery_user(db):
    return User.objects.create_user(
        phone="+201001234571",
        role="DELIVERY",
        is_active=True,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        phone="+201001234572",
        role="ADMIN",
        is_active=True,
    )
    
    
