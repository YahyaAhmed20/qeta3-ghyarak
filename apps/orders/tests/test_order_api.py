import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.orders.models import Order
from apps.orders.models import Order, OrderItem

@pytest.mark.django_db
def test_customer_can_list_own_orders(customer, order):
    client = APIClient()
    client.force_authenticate(user=customer)

    response = client.get("/api/v1/orders/")

    assert response.status_code == 200

    data = response.data

    assert data["count"] == 1
    assert len(data["results"]) == 1

    result = data["results"][0]

    assert result["id"] == str(order.id)
    assert result["order_number"] == order.order_number
    assert result["status"] == order.status
    assert result["total"] == "250.00"
    
@pytest.mark.django_db
def test_customer_cannot_see_another_customer_orders(customer, order):
    another_customer = User.objects.create_user(
        phone="+201001234570",
        role="CUSTOMER",
    )

    client = APIClient()
    client.force_authenticate(user=another_customer)

    response = client.get("/api/v1/orders/")

    assert response.status_code == 200
    assert response.data["count"] == 0
    assert response.data["results"] == []
    
    
@pytest.mark.django_db
def test_non_customer_cannot_list_orders(seller_owner):
    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.get("/api/v1/orders/")

    assert response.status_code == 403
    assert response.data["detail"] == "Only customers can view orders."
    
    
@pytest.mark.django_db
def test_customer_can_retrieve_own_order(customer, order):
    client = APIClient()
    client.force_authenticate(user=customer)

    response = client.get(f"/api/v1/orders/{order.id}/")

    assert response.status_code == 200

    data = response.data

    assert data["id"] == str(order.id)
    assert data["order_number"] == order.order_number
    assert data["status"] == order.status
    assert data["subtotal"] == "250.00"
    assert data["delivery_fee"] == "0.00"
    assert data["total"] == "250.00"
    
    
@pytest.mark.django_db
def test_customer_cannot_retrieve_another_customer_order(customer, order):
    another_customer = User.objects.create_user(
        phone="+201001234570",
        role="CUSTOMER",
    )

    client = APIClient()
    client.force_authenticate(user=another_customer)

    response = client.get(f"/api/v1/orders/{order.id}/")

    assert response.status_code == 404
    assert response.data["detail"] == "Order not found."
    
    
@pytest.mark.django_db
def test_customer_order_detail_includes_items(
    customer,
    order,
    seller_product,
):
    OrderItem.objects.create(
        order=order,
        seller_product=seller_product,
        product_name_snapshot="Bosch Oil Filter",
        part_number_snapshot="06J-115-403-Q",
        unit_price="250.00",
        discount="0.00",
        quantity=2,
    )

    client = APIClient()
    client.force_authenticate(user=customer)

    response = client.get(f"/api/v1/orders/{order.id}/")

    assert response.status_code == 200
    assert "items" in response.data
    assert len(response.data["items"]) == 1

    item = response.data["items"][0]

    assert item["product_name"] == "Bosch Oil Filter"
    assert item["part_number"] == "06J-115-403-Q"
    assert item["unit_price"] == "250.00"
    assert item["quantity"] == 2
    assert item["subtotal"] == "500.00"
    
    
@pytest.mark.django_db
def test_customer_order_detail_returns_empty_items_when_order_has_no_items(
    customer,
    order,
):
    client = APIClient()
    client.force_authenticate(user=customer)

    response = client.get(f"/api/v1/orders/{order.id}/")

    assert response.status_code == 200
    assert response.data["items"] == []