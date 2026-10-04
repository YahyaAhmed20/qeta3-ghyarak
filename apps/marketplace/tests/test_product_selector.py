import uuid

import pytest

from apps.accounts.models import User
from apps.catalog.models import Product
from apps.inventory.models import Inventory
from apps.marketplace.selectors.product import MarketplaceProductSelector
from apps.stores.models import SellerProduct, Store, StoreStatus


@pytest.mark.django_db
def test_get_products_returns_active_marketplace_products(
    active_store,
    active_product,
):
    seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )

    Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=2,
    )

    products = MarketplaceProductSelector.get_products()

    assert list(products) == [active_product]


@pytest.mark.django_db
def test_get_products_excludes_inactive_products(
    active_store,
    active_product,
    inactive_product,
):
    SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )

    SellerProduct.objects.create(
        store=active_store,
        product=inactive_product,
        price="300.00",
    )

    products = MarketplaceProductSelector.get_products()

    assert active_product in products
    assert inactive_product not in products


@pytest.mark.django_db
def test_get_products_excludes_inactive_seller_products(
    active_store,
    active_product,
):
    SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
        is_active=False,
    )

    products = MarketplaceProductSelector.get_products()

    assert list(products) == []


@pytest.mark.django_db
def test_get_products_excludes_unverified_store(
    active_store,
    active_product,
):
    active_store.is_verified = False
    active_store.save(update_fields=["is_verified"])

    SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )

    products = MarketplaceProductSelector.get_products()

    assert list(products) == []


@pytest.mark.django_db
def test_get_products_excludes_inactive_store(
    active_store,
    active_product,
):
    active_store.status = StoreStatus.SUSPENDED
    active_store.save(update_fields=["status"])

    SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )

    products = MarketplaceProductSelector.get_products()

    assert list(products) == []


@pytest.mark.django_db
def test_get_products_returns_product_from_multiple_stores(
    active_store,
    active_product,
):
    second_owner = User.objects.create_user(
        phone="+201001234568",
        role="SELLER_OWNER",
    )

    second_store = Store.objects.create(
        owner=second_owner,
        name="Beta Spare Parts",
        slug="beta-spare-parts",
        phone="+201001234568",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )

    SellerProduct.objects.create(
        store=second_store,
        product=active_product,
        price="230.00",
    )

    products = MarketplaceProductSelector.get_products()

    assert list(products) == [active_product]


# ---------------------------------------------------------------------------
# get_product_detail tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_product_detail_returns_product(
    marketplace_seller_product,
):
    result = MarketplaceProductSelector.get_product_detail(
        product_id=marketplace_seller_product.product.id,
    )

    assert result is not None
    assert result.id == marketplace_seller_product.product.id


@pytest.mark.django_db
def test_get_product_detail_excludes_inactive_seller_product(
    marketplace_seller_product,
    active_product,
):
    second_owner = User.objects.create_user(
        phone="+201001234568",
        role="SELLER_OWNER",
    )
    second_store = Store.objects.create(
        owner=second_owner,
        name="Beta Spare Parts",
        slug="beta-spare-parts",
        phone="+201001234568",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    inactive_seller_product = SellerProduct.objects.create(
        store=second_store,
        product=active_product,
        price="2100.00",
        is_active=False,
    )
    Inventory.objects.create(
        seller_product=inactive_seller_product,
        on_hand=10,
        reserved=0,
    )

    result = MarketplaceProductSelector.get_product_detail(
        product_id=active_product.id,
    )

    sellers = list(result.seller_products.all())

    assert len(sellers) == 1
    assert sellers[0].id == marketplace_seller_product.id


@pytest.mark.django_db
def test_get_product_detail_excludes_seller_with_no_available_stock(
    marketplace_seller_product,
    active_product,
):
    second_owner = User.objects.create_user(
        phone="+201001234568",
        role="SELLER_OWNER",
    )
    second_store = Store.objects.create(
        owner=second_owner,
        name="Beta Spare Parts",
        slug="beta-spare-parts",
        phone="+201001234568",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    unavailable_seller_product = SellerProduct.objects.create(
        store=second_store,
        product=active_product,
        price="2100.00",
        is_active=True,
    )
    Inventory.objects.create(
        seller_product=unavailable_seller_product,
        on_hand=5,
        reserved=5,
    )

    result = MarketplaceProductSelector.get_product_detail(
        product_id=active_product.id,
    )

    sellers = list(result.seller_products.all())

    assert len(sellers) == 1
    assert sellers[0].id == marketplace_seller_product.id


@pytest.mark.django_db
def test_get_product_detail_excludes_seller_without_inventory(
    marketplace_seller_product,
    active_product,
):
    second_owner = User.objects.create_user(
        phone="+201001234568",
        role="SELLER_OWNER",
    )
    second_store = Store.objects.create(
        owner=second_owner,
        name="Beta Spare Parts",
        slug="beta-spare-parts",
        phone="+201001234568",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    seller_without_inventory = SellerProduct.objects.create(
        store=second_store,
        product=active_product,
        price="2100.00",
        is_active=True,
    )

    result = MarketplaceProductSelector.get_product_detail(
        product_id=active_product.id,
    )

    sellers = list(result.seller_products.all())

    assert len(sellers) == 1
    assert sellers[0].id == marketplace_seller_product.id


@pytest.mark.django_db
def test_get_product_detail_returns_none_when_no_available_seller(
    active_store,
    active_product,
):
    seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="2100.00",
        is_active=True,
    )
    Inventory.objects.create(
        seller_product=seller_product,
        on_hand=5,
        reserved=5,
    )

    result = MarketplaceProductSelector.get_product_detail(
        product_id=active_product.id,
    )

    assert result is None


@pytest.mark.django_db
def test_get_product_detail_returns_none_for_unknown_product():
    result = MarketplaceProductSelector.get_product_detail(
        product_id=uuid.uuid4(),
    )

    assert result is None