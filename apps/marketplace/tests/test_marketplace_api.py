import uuid
import pytest
from rest_framework.test import APIClient
from apps.accounts.models.user import User
from apps.catalog.models import (
    Brand,
    Category,
    Product,
    ProductPartNumber,
    ProductCompatibility,
    CompatibilityStatus,
)
from apps.stores.models.seller_product import SellerProduct
from apps.stores.models.store import Store, StoreStatus
from apps.inventory.models import Inventory


@pytest.mark.django_db
def test_marketplace_product_list_returns_available_product(
    marketplace_seller_product,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/"
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 1

    product = response.data["results"][0]

    assert product["id"] == str(
        marketplace_seller_product.product.id
    )
    assert product["name"] == "Bosch Oil Filter"
    assert len(product["sellers"]) == 1

    seller = product["sellers"][0]

    assert seller["store_name"] == "Alfa Spare Parts"
    assert seller["city"] == "Suez"
    assert seller["price"] == "2300.00"
    assert seller["sale_price"] == "2200.00"
    assert seller["available"] == 10


@pytest.mark.django_db
def test_marketplace_product_list_searches_by_name(
    marketplace_seller_product,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/?search=Oil"
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 1

    product = response.data["results"][0]

    assert product["name"] == "Bosch Oil Filter"


@pytest.mark.django_db
def test_marketplace_product_list_search_returns_empty_for_no_match(
    marketplace_seller_product,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/?search=Brake"
    )

    assert response.status_code == 200
    assert response.data["results"] == []


@pytest.fixture
def marketplace_part_number(marketplace_seller_product):
    return ProductPartNumber.objects.create(
        product=marketplace_seller_product.product,
        part_number="90915-YZZD1",
        number_type="OEM",
        brand=marketplace_seller_product.product.brand,
    )


@pytest.mark.django_db
def test_marketplace_product_list_searches_by_part_number(
    marketplace_part_number,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/?search=90915-YZZD1"
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 1

    product = response.data["results"][0]

    assert product["name"] == "Bosch Oil Filter"


@pytest.mark.django_db
def test_marketplace_product_list_searches_normalized_part_number(
    marketplace_part_number,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/?search=90915 yzzd1"
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 1

    assert response.data["results"][0]["name"] == "Bosch Oil Filter"


@pytest.mark.django_db
def test_marketplace_product_list_filters_by_category(
    marketplace_seller_product,
    category,
):
    client = APIClient()

    response = client.get(
        f"/api/v1/marketplace/products/?category={category.id}"
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 1

    assert response.data["results"][0]["name"] == "Bosch Oil Filter"


@pytest.mark.django_db
def test_marketplace_product_list_returns_empty_for_other_category(
    marketplace_seller_product,
    other_category,
):
    client = APIClient()

    response = client.get(
        f"/api/v1/marketplace/products/?category={other_category.id}"
    )

    assert response.status_code == 200
    assert response.data["results"] == []


@pytest.mark.django_db
def test_marketplace_product_list_filters_by_brand(
    marketplace_seller_product,
    brand,
):
    client = APIClient()

    response = client.get(
        f"/api/v1/marketplace/products/?brand={brand.id}"
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Bosch Oil Filter"


@pytest.mark.django_db
def test_marketplace_product_list_returns_empty_for_other_brand(
    marketplace_seller_product,
):
    other_brand = Brand.objects.create(
        name="Mann",
        slug="mann",
    )

    client = APIClient()

    response = client.get(
        f"/api/v1/marketplace/products/?brand={other_brand.id}"
    )

    assert response.status_code == 200
    assert response.data["results"] == []


@pytest.mark.django_db
def test_marketplace_product_list_filters_by_vehicle(
    product_compatibility,
    vehicle_variant,
):
    client = APIClient()

    response = client.get(
        f"/api/v1/marketplace/products/?vehicle={vehicle_variant.id}"
    )

    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == "Bosch Oil Filter"


@pytest.mark.django_db
def test_marketplace_product_list_returns_empty_for_incompatible_vehicle(
    marketplace_seller_product,
    vehicle_variant,
):
    client = APIClient()

    response = client.get(
        f"/api/v1/marketplace/products/?vehicle={vehicle_variant.id}"
    )

    assert response.status_code == 200
    assert response.data["results"] == []


@pytest.mark.django_db
def test_marketplace_product_list_is_paginated(
    marketplace_seller_product,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/?page=1&page_size=1"
    )

    assert response.status_code == 200

    assert response.data["count"] == 1
    assert response.data["next"] is None
    assert response.data["previous"] is None
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_marketplace_product_pagination(
    paginated_marketplace_products,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/?page=1&page_size=20"
    )

    assert response.status_code == 200
    assert response.data["count"] == 21
    assert len(response.data["results"]) == 20
    assert response.data["previous"] is None
    assert response.data["next"] is not None

    response = client.get(
        "/api/v1/marketplace/products/?page=2&page_size=20"
    )

    assert response.status_code == 200
    assert response.data["count"] == 21
    assert len(response.data["results"]) == 1
    assert response.data["previous"] is not None
    assert response.data["next"] is None


@pytest.mark.django_db
def test_marketplace_product_returns_min_price(
    marketplace_seller_product,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/"
    )

    assert response.status_code == 200
    result = response.data["results"][0]

    assert result["min_price"] == "2200.00"


@pytest.mark.django_db
def test_marketplace_product_min_price_uses_cheapest_seller(
    marketplace_seller_product,
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

    second_seller_product = SellerProduct.objects.create(
        store=second_store,
        product=active_product,
        price="2100.00",
        sale_price=None,
        is_active=True,
    )

    Inventory.objects.create(
        seller_product=second_seller_product,
        on_hand=10,
        reserved=0,
    )

    response = APIClient().get(
        "/api/v1/marketplace/products/"
    )

    assert response.status_code == 200

    result = response.data["results"][0]

    assert result["min_price"] == "2100.00"


@pytest.mark.django_db
def test_marketplace_products_can_be_sorted_by_price(
    marketplace_seller_product,
    active_store,
    active_product,
):
    second_owner = User.objects.create_user(
        phone="+201001234569",
        role="SELLER_OWNER",
    )

    second_store = Store.objects.create(
        owner=second_owner,
        name="Gamma Spare Parts",
        slug="gamma-spare-parts",
        phone="+201001234569",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    second_product = Product.objects.create(
        category=active_product.category,
        brand=active_product.brand,
        name="Cheaper Brake Pad",
        slug="cheaper-brake-pad",
        product_type="AFTERMARKET",
        is_active=True,
    )

    second_seller_product = SellerProduct.objects.create(
        store=second_store,
        product=second_product,
        price="1500.00",
        is_active=True,
    )

    Inventory.objects.create(
        seller_product=second_seller_product,
        on_hand=10,
        reserved=0,
    )

    response = APIClient().get(
        "/api/v1/marketplace/products/?ordering=price"
    )

    assert response.status_code == 200

    results = response.data["results"]

    assert results[0]["id"] == str(second_product.id)
    assert results[0]["min_price"] == "1500.00"


@pytest.mark.django_db
def test_marketplace_products_can_be_sorted_by_price_descending(
    marketplace_seller_product,
    active_product,
):
    second_owner = User.objects.create_user(
        phone="+201001234570",
        role="SELLER_OWNER",
    )

    second_store = Store.objects.create(
        owner=second_owner,
        name="Delta Spare Parts",
        slug="delta-spare-parts",
        phone="+201001234570",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    second_product = Product.objects.create(
        category=active_product.category,
        brand=active_product.brand,
        name="Cheaper Brake Pad",
        slug="cheaper-brake-pad",
        product_type="AFTERMARKET",
        is_active=True,
    )

    second_seller_product = SellerProduct.objects.create(
        store=second_store,
        product=second_product,
        price="1500.00",
        is_active=True,
    )

    Inventory.objects.create(
        seller_product=second_seller_product,
        on_hand=10,
        reserved=0,
    )

    response = APIClient().get(
        "/api/v1/marketplace/products/?ordering=-price"
    )

    assert response.status_code == 200

    results = response.data["results"]

    assert results[0]["id"] == str(marketplace_seller_product.product.id)
    assert results[0]["min_price"] == "2200.00"


@pytest.mark.django_db
def test_marketplace_products_invalid_ordering_falls_back_to_name(
    marketplace_seller_product,
):
    response = APIClient().get(
        "/api/v1/marketplace/products/?ordering=hack"
    )

    assert response.status_code == 200

    results = response.data["results"]

    assert len(results) == 1
    assert results[0]["name"] == "Bosch Oil Filter"


@pytest.mark.django_db
def test_marketplace_product_detail_returns_product(
    client,
    marketplace_seller_product,
):
    product = marketplace_seller_product.product

    response = client.get(
        f"/api/v1/marketplace/products/{product.id}/"
    )

    assert response.status_code == 200
    assert response.data["id"] == str(product.id)
    assert response.data["name"] == product.name
    assert response.data["min_price"] == "2200.00"
    assert len(response.data["sellers"]) == 1


@pytest.mark.django_db
def test_marketplace_product_detail_returns_404_for_unknown_product(
    client,
):
    response = client.get(
        f"/api/v1/marketplace/products/{uuid.uuid4()}/"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_marketplace_product_detail_returns_404_when_no_available_seller(
    client,
    active_store,
    active_product,
):
    seller_product = SellerProduct.objects.create(
        store=active_store,
        product=active_product,
        price="2100.00",
    )

    Inventory.objects.create(
        seller_product=seller_product,
        on_hand=5,
        reserved=5,
    )

    response = client.get(
        f"/api/v1/marketplace/products/{active_product.id}/"
    )

    assert response.status_code == 404
    
    
    
@pytest.mark.django_db
def test_marketplace_product_list_excludes_seller_with_no_available_stock(
    client,
    marketplace_seller_product,
    active_store,
    active_product,
):
    unavailable_seller_product = SellerProduct.objects.create(
        store=Store.objects.create(
            owner=User.objects.create_user(
                phone="+201001234568",
                role="SELLER_OWNER",
            ),
            name="Beta Spare Parts",
            slug="beta-spare-parts",
            phone="+201001234568",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        ),
        product=active_product,
        price="2100.00",
        is_active=True,
    )

    Inventory.objects.create(
        seller_product=unavailable_seller_product,
        on_hand=5,
        reserved=5,
    )

    response = client.get(
        "/api/v1/marketplace/products/"
    )

    assert response.status_code == 200

    product = next(
        item
        for item in response.data["results"]
        if item["id"] == str(active_product.id)
    )

    assert len(product["sellers"]) == 1
    assert (
        product["sellers"][0]["store_name"]
        == marketplace_seller_product.store.name
    )
    
@pytest.mark.django_db
def test_marketplace_product_detail_returns_product_with_sellers(
    marketplace_seller_product,
):
    client = APIClient()

    response = client.get(
        f"/api/v1/marketplace/products/{marketplace_seller_product.product.id}/"
    )

    assert response.status_code == 200

    data = response.data

    assert data["id"] == str(marketplace_seller_product.product.id)
    assert data["name"] == marketplace_seller_product.product.name

    assert "sellers" in data
    assert len(data["sellers"]) == 1

    seller = data["sellers"][0]

    assert seller["store_name"] == marketplace_seller_product.store.name
    assert seller["price"] == "2300.00"
    assert seller["sale_price"] == "2200.00"
    assert seller["available"] == 10