import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from apps.addresses.models import Address
from apps.cart.constants import CartStatus
from apps.cart.models import Cart
from apps.cart.services.cart_item import CartItemService
from apps.catalog.models import ProductPartNumber, PartNumberType
from apps.inventory.models import Inventory
from apps.orders.models import Order, OrderItem
from apps.stores.models import SellerProduct


@pytest.fixture
def address(customer):
    return Address.objects.create(
        customer=customer,
        label="Home",
        recipient_name="Test Customer",
        phone="+201001234568",
        city="Suez",
        area="Arbaeen",
        address_line="Test Street",
        building="10",
        floor="2",
        apartment="5",
        landmark="Near Test",
        latitude="29.9668",
        longitude="32.5498",
        is_default=True,
    )


@pytest.fixture
def cart(customer, active_store):
    return Cart.objects.create(
        customer=customer,
        store=active_store,
        status=CartStatus.ACTIVE,
    )


@pytest.fixture
def checkout_inventory(cart, seller_product):
    inventory = Inventory.objects.create(
        seller_product=seller_product,
        on_hand=10,
        reserved=0,
    )

    CartItemService.add_item(
        cart=cart,
        seller_product=seller_product,
        quantity=2,
    )

    return inventory


@pytest.fixture
def part_number(active_product):
    return ProductPartNumber.objects.create(
        product=active_product,
        part_number="06J-115-403-Q",
        number_type=PartNumberType.OEM,
        is_active=True,
    )


@pytest.mark.django_db
class TestCheckoutAPI:

    def test_unauthenticated_user_cannot_checkout(self, address):
        client = APIClient()

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
            },
            format="json",
        )

        assert response.status_code == 401

    def test_non_customer_cannot_checkout(
        self,
        seller_owner,
        address,
    ):
        client = APIClient()
        client.force_authenticate(user=seller_owner)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
            },
            format="json",
        )

        assert response.status_code == 403

    def test_checkout_requires_address_id(self, customer):
        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {},
            format="json",
        )

        assert response.status_code == 400
        assert "address_id" in response.data

    def test_checkout_rejects_invalid_address(
        self,
        customer,
    ):
        import uuid

        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(uuid.uuid4()),
            },
            format="json",
        )

        assert response.status_code == 404

    def test_customer_cannot_checkout_using_another_customers_address(
        self,
        customer,
        active_store,
        address,
    ):
        other_customer = type(customer).objects.create_user(
            phone="+201001234599",
            role="CUSTOMER",
        )

        client = APIClient()
        client.force_authenticate(user=other_customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
            },
            format="json",
        )

        assert response.status_code == 404

    def test_checkout_requires_active_cart(
        self,
        customer,
        address,
    ):
        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
            },
            format="json",
        )

        assert response.status_code == 400

    def test_checkout_rejects_empty_cart(
        self,
        customer,
        active_store,
        address,
        cart,
    ):
        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
            },
            format="json",
        )

        assert response.status_code == 400

    def test_successful_checkout(
        self,
        customer,
        active_store,
        address,
        cart,
        seller_product,
        checkout_inventory,
        part_number,
    ):
        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
                "notes": "Call before delivery",
            },
            format="json",
        )

        assert response.status_code == 201

        data = response.data

        assert data["status"] == "CREATED"
        assert data["subtotal"] == "500.00"
        assert data["delivery_fee"] == "0.00"
        assert data["total"] == "500.00"

        order = Order.objects.get(id=data["id"])

        assert order.customer_id == customer.id
        assert order.store_id == active_store.id
        assert order.notes == "Call before delivery"

        assert order.subtotal == Decimal("500.00")
        assert order.total == Decimal("500.00")
        assert order.delivery_fee == Decimal("0.00")

        assert order.address_snapshot["recipient_name"] == "Test Customer"
        assert order.address_snapshot["phone"] == "+201001234568"
        assert order.address_snapshot["city"] == "Suez"
        assert order.address_snapshot["area"] == "Arbaeen"
        assert order.address_snapshot["address_line"] == "Test Street"
        assert order.address_snapshot["building"] == "10"
        assert order.address_snapshot["floor"] == "2"
        assert order.address_snapshot["apartment"] == "5"

        item = OrderItem.objects.get(order=order)

        assert item.seller_product_id == seller_product.id
        assert item.product_name_snapshot == "Bosch Oil Filter"
        assert item.part_number_snapshot == "06J-115-403-Q"
        assert item.unit_price == Decimal("250.00")
        assert item.quantity == 2

        cart.refresh_from_db()

        assert cart.status == CartStatus.CONVERTED

        checkout_inventory.refresh_from_db()

        assert checkout_inventory.on_hand == 10
        assert checkout_inventory.reserved == 2
        assert checkout_inventory.available == 8

    def test_client_cannot_control_delivery_fee(
        self,
        customer,
        active_store,
        address,
        cart,
        seller_product,
        checkout_inventory,
        part_number,
    ):
        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
                "delivery_fee": "9999.00",
            },
            format="json",
        )

        assert response.status_code == 201

        order = Order.objects.get(id=response.data["id"])

        assert order.delivery_fee == Decimal("0.00")
        assert order.total == Decimal("500.00")

    def test_checkout_rejects_outdated_cart_price(
        self,
        customer,
        active_store,
        address,
        cart,
        seller_product,
        part_number,
    ):
        inventory = Inventory.objects.create(
            seller_product=seller_product,
            on_hand=10,
            reserved=0,
        )

        CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        seller_product.price = Decimal("300.00")
        seller_product.save(update_fields=["price"])

        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
            },
            format="json",
        )

        assert response.status_code == 400

        inventory.refresh_from_db()

        assert inventory.reserved == 0

        assert not Order.objects.filter(
            customer=customer,
            status="CREATED",
        ).exists()

    def test_checkout_rejects_insufficient_stock(
        self,
        customer,
        active_store,
        address,
        cart,
        seller_product,
        part_number,
    ):
        inventory = Inventory.objects.create(
            seller_product=seller_product,
            on_hand=1,
            reserved=0,
        )

        CartItemService.add_item(
            cart=cart,
            seller_product=seller_product,
            quantity=2,
        )

        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
            },
            format="json",
        )

        assert response.status_code == 400

        inventory.refresh_from_db()

        assert inventory.on_hand == 1
        assert inventory.reserved == 0

        assert not Order.objects.filter(
            customer=customer,
            status="CREATED",
        ).exists()

    def test_checkout_rejects_notes_longer_than_1000_characters(
        self,
        customer,
        address,
    ):
        client = APIClient()
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/orders/checkout/",
            {
                "address_id": str(address.id),
                "notes": "x" * 1001,
            },
            format="json",
        )

        assert response.status_code == 400
        assert "notes" in response.data