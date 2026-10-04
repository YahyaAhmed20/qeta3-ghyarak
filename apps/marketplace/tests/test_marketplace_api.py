import pytest
from rest_framework.test import APIClient
from apps.catalog.models import ProductPartNumber
from apps.catalog.models import Brand
@pytest.mark.django_db
def test_marketplace_product_list_returns_available_product(
    marketplace_seller_product,
):
    client = APIClient()

    response = client.get(
        "/api/v1/marketplace/products/"
    )

    assert response.status_code == 200
    assert len(response.data) == 1

    product = response.data[0]

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
    assert len(response.data) == 1

    product = response.data[0]

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
    assert response.data == []
    
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
    assert len(response.data) == 1

    product = response.data[0]

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
    assert len(response.data) == 1

    assert response.data[0]["name"] == "Bosch Oil Filter"
    
    
    
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
    assert len(response.data) == 1

    assert response.data[0]["name"] == "Bosch Oil Filter"
    
    
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
    assert response.data == []
    
    
    
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
    assert len(response.data) == 1
    assert response.data[0]["name"] == "Bosch Oil Filter"
    
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
    assert response.data == []
    
    
    
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
    assert len(response.data) == 1
    assert response.data[0]["name"] == "Bosch Oil Filter"
    
    
    
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
    assert response.data == []