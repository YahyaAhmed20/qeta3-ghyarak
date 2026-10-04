import pytest

from apps.inventory.models import Inventory
from apps.marketplace.api.serializers import MarketplaceProductSerializer
from apps.stores.models import SellerProduct


@pytest.mark.django_db
def test_marketplace_product_serializer_returns_product_data(
    active_store,
    active_product,
):
    seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
        sale_price="225.00",
    )

    Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=2,
    )

    data = MarketplaceProductSerializer(active_product).data

    assert data["id"] == str(active_product.id)
    assert data["name"] == "Bosch Oil Filter"
    assert data["slug"] == "bosch-oil-filter"
    assert data["brand"] == "Bosch"
    assert data["category"] == "Filters"
    assert data["product_type"] == "AFTERMARKET"

    assert len(data["sellers"]) == 1

    seller = data["sellers"][0]

    assert seller["store_name"] == "Alfa Spare Parts"
    assert seller["city"] == "Suez"
    assert seller["price"] == "250.00"
    assert seller["sale_price"] == "225.00"
    assert seller["available"] == 8


@pytest.mark.django_db
def test_marketplace_product_serializer_supports_multiple_sellers(
    active_store,
    active_product,
):
    from apps.accounts.models import User
    from apps.stores.models import Store, StoreStatus

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

    first_seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="250.00",
    )

    second_seller_product = SellerProduct.objects.create(
        store=second_store,
        product=active_product,
        price="230.00",
    )

    Inventory.objects.create(
        seller_product=first_seller_product,
        on_hand=10,
        reserved=2,
    )

    Inventory.objects.create(
        seller_product=second_seller_product,
        on_hand=5,
        reserved=1,
    )

    data = MarketplaceProductSerializer(active_product).data

    assert len(data["sellers"]) == 2

    stores = {
        seller["store_name"]
        for seller in data["sellers"]
    }

    assert stores == {
        "Alfa Spare Parts",
        "Beta Spare Parts",
    }