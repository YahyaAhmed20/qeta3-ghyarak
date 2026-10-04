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