from decimal import Decimal

from apps.finance.models import Commission
from apps.inventory.models.inventory import Inventory
import pytest
from rest_framework.test import APIClient
from apps.orders.models import Order, OrderItem
from apps.orders.models import Order
from apps.accounts.models import User
from apps.orders.models import Order
from apps.stores.models import Store, StoreStatus
import uuid
@pytest.mark.django_db
def test_seller_can_list_store_orders(seller_owner, active_store, order):
    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.get("/api/v1/seller/orders/")

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
def test_seller_cannot_see_another_store_orders(
    seller_owner,
    active_store,
    order,
):
    another_seller = User.objects.create_user(
        phone="+201001234571",
        role="SELLER_OWNER",
    )

    another_store = Store.objects.create(
        owner=another_seller,
        name="Beta Spare Parts",
        slug="beta-spare-parts-seller-orders",
        phone="+201001234571",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    another_order = Order.objects.create(
        customer=order.customer,
        store=another_store,
        subtotal="500.00",
        seller_discount="0.00",
        platform_discount="0.00",
        delivery_fee="0.00",
        total="500.00",
        address_snapshot={"city": "Suez"},
    )

    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.get("/api/v1/seller/orders/")

    assert response.status_code == 200
    assert response.data["count"] == 1

    order_ids = [
        item["id"]
        for item in response.data["results"]
    ]

    assert str(order.id) in order_ids
    assert str(another_order.id) not in order_ids
    
    
@pytest.mark.django_db
def test_customer_cannot_list_seller_orders(customer):
    client = APIClient()
    client.force_authenticate(user=customer)

    response = client.get("/api/v1/seller/orders/")

    assert response.status_code == 403
    assert response.data["detail"] == "Only sellers can view store orders."
    
    
@pytest.mark.django_db
def test_unauthenticated_cannot_list_seller_orders():
    client = APIClient()

    response = client.get("/api/v1/seller/orders/")

    assert response.status_code == 401
    
@pytest.mark.django_db
def test_seller_can_retrieve_own_store_order(
    seller_owner,
    active_store,
    order,
):
    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.get(
        f"/api/v1/seller/orders/{order.id}/"
    )

    assert response.status_code == 200

    data = response.data

    assert data["id"] == str(order.id)
    assert data["order_number"] == order.order_number
    assert data["status"] == order.status
    assert data["total"] == "250.00"
    
@pytest.mark.django_db
def test_seller_cannot_retrieve_another_store_order(
    seller_owner,
    order,
):
    another_seller = User.objects.create_user(
        phone="+201001234571",
        role="SELLER_OWNER",
    )

    another_store = Store.objects.create(
        owner=another_seller,
        name="Beta Spare Parts",
        slug="beta-spare-parts-detail",
        phone="+201001234571",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    another_order = Order.objects.create(
        customer=order.customer,
        store=another_store,
        subtotal="500.00",
        seller_discount="0.00",
        platform_discount="0.00",
        delivery_fee="0.00",
        total="500.00",
        address_snapshot={"city": "Suez"},
    )

    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.get(
        f"/api/v1/seller/orders/{another_order.id}/"
    )

    assert response.status_code == 404
    assert response.data["detail"] == "Order not found."
    
    
@pytest.mark.django_db
def test_seller_order_detail_includes_items(
    seller_owner,
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
    client.force_authenticate(user=seller_owner)

    response = client.get(
        f"/api/v1/seller/orders/{order.id}/"
    )

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
def test_seller_order_detail_returns_empty_items_when_order_has_no_items(
    seller_owner,
    order,
):
    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.get(
        f"/api/v1/seller/orders/{order.id}/"
    )

    assert response.status_code == 200
    assert response.data["items"] == []
    
    
@pytest.mark.django_db
def test_seller_can_accept_own_store_order(
    seller_owner,
    order,
):
    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.post(
        f"/api/v1/seller/orders/{order.id}/accept/"
    )

    assert response.status_code == 200
    assert response.data["status"] == "ACCEPTED"

    order.refresh_from_db()

    assert order.status == "ACCEPTED"
    
@pytest.mark.django_db
def test_seller_cannot_accept_another_store_order(
    seller_owner,
    order,
):
    another_seller = User.objects.create_user(
        phone="+201001234571",
        role="SELLER_OWNER",
    )

    another_store = Store.objects.create(
        owner=another_seller,
        name="Beta Spare Parts",
        slug="beta-spare-parts-accept",
        phone="+201001234571",
        address="Suez",
        city="Suez",
        status=StoreStatus.ACTIVE,
        is_verified=True,
    )

    another_order = Order.objects.create(
        customer=order.customer,
        store=another_store,
        subtotal="500.00",
        seller_discount="0.00",
        platform_discount="0.00",
        delivery_fee="0.00",
        total="500.00",
        address_snapshot={"city": "Suez"},
    )

    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.post(
        f"/api/v1/seller/orders/{another_order.id}/accept/"
    )

    assert response.status_code == 403
    assert response.data["detail"] == (
        "Actor does not have access to this order."
    )

    another_order.refresh_from_db()

    assert another_order.status == "CREATED"
    

@pytest.mark.django_db
def test_seller_can_move_accepted_order_to_preparing(
    seller_owner,
    order,
):
    order.status = "ACCEPTED"
    order.save(update_fields=["status", "updated_at"])

    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.post(
        f"/api/v1/seller/orders/{order.id}/preparing/"
    )

    assert response.status_code == 200
    assert response.data["status"] == "PREPARING"

    order.refresh_from_db()

    assert order.status == "PREPARING"
    
@pytest.mark.django_db
def test_seller_cannot_move_created_order_to_preparing(
    seller_owner,
    order,
):
    order.status = "CREATED"
    order.save(update_fields=["status", "updated_at"])

    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.post(
        f"/api/v1/seller/orders/{order.id}/preparing/"
    )

    assert response.status_code == 400

    order.refresh_from_db()

    assert order.status == "CREATED"
    
@pytest.mark.django_db
def test_seller_can_move_preparing_order_to_ready(
    seller_owner,
    order,
):
    order.status = "PREPARING"
    order.save(update_fields=["status", "updated_at"])

    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.post(
        f"/api/v1/seller/orders/{order.id}/ready/"
    )

    assert response.status_code == 200
    assert response.data["status"] == "READY"

    order.refresh_from_db()

    assert order.status == "READY"
    
@pytest.mark.django_db
def test_seller_can_move_ready_order_to_out_for_delivery(
    seller_owner,
    order,
):
    order.status = "READY"
    order.save(update_fields=["status", "updated_at"])

    print("ROLE:", seller_owner.role)
    print("SELLER ID:", seller_owner.id)
    print("STORE OWNER ID:", order.store.owner_id)
    print("ORDER STORE:", order.store_id)

    client = APIClient()
    client.force_authenticate(user=seller_owner)

    response = client.post(
        f"/api/v1/seller/orders/{order.id}/out-for-delivery/"
    )

    assert response.status_code == 200
    
    
@pytest.mark.django_db
def test_seller_staff_cannot_move_ready_order_to_out_for_delivery(
    seller_staff,
    order,
):
    order.status = "READY"
    order.save(update_fields=["status", "updated_at"])

    client = APIClient()
    client.force_authenticate(user=seller_staff)

    response = client.post(
        f"/api/v1/seller/orders/{order.id}/out-for-delivery/"
    )

    assert response.status_code == 403

    order.refresh_from_db()

    assert order.status == "READY"
    
    
@pytest.fixture
def seller_staff(db, seller_owner):
    return User.objects.create_user(
        phone="+201001234572",
        role="SELLER_STAFF",
    )
    
    

@pytest.mark.django_db
def test_delivery_cannot_complete_order_without_otp(
    delivery_user,
    order,
):
    order.status = "OUT_FOR_DELIVERY"
    order.save(update_fields=["status", "updated_at"])

    client = APIClient()
    client.force_authenticate(user=delivery_user)

    response = client.post(
        f"/api/v1/orders/delivery/assignments/"
        f"{uuid.uuid4()}/complete/",
        {},
        format="json",
    )

    assert response.status_code == 400
    
@pytest.mark.django_db
def test_delivery_user_can_accept_assignment(
    delivery_user,
    delivery_assignment,
):
    client = APIClient()
    client.force_authenticate(user=delivery_user)

    response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/accept/"
    )

    assert response.status_code == 200
    assert response.data["status"] == "ACCEPTED"

    delivery_assignment.refresh_from_db()

    assert delivery_assignment.status == "ACCEPTED"
    assert delivery_assignment.accepted_at is not None
    
    
@pytest.mark.django_db
def test_delivery_cannot_complete_without_otp(
    delivery_user,
    delivery_assignment,
):
    client = APIClient()
    client.force_authenticate(user=delivery_user)

    # Assignment must be ACCEPTED first
    accept_response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/accept/"
    )

    assert accept_response.status_code == 200

    response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/complete/",
        {},
        format="json",
    )

    assert response.status_code == 400
    
    
@pytest.mark.django_db
def test_delivery_user_can_complete_order_with_valid_otp(
    delivery_user,
    delivery_assignment,
    commission_rule,
):
    client = APIClient()
    client.force_authenticate(user=delivery_user)

    # Accept delivery assignment
    accept_response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/accept/"
    )

    assert accept_response.status_code == 200

    delivery_assignment.refresh_from_db()
    assert delivery_assignment.status == "ACCEPTED"

    # Create real delivery OTP
    from apps.orders.services.delivery_otp import DeliveryOTPService

    order = delivery_assignment.order
    otp, code = DeliveryOTPService.create(order=order)

    response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/complete/",
        {
            "otp_id": str(otp.id),
            "code": code,
        },
        format="json",
    )

    print(response.data)

    assert response.status_code == 200
    assert response.data["status"] == "DELIVERED"

    order.refresh_from_db()
    delivery_assignment.refresh_from_db()
    otp.refresh_from_db()

    assert order.status == "DELIVERED"
    assert delivery_assignment.status == "DELIVERED"
    assert otp.status == "VERIFIED"
    assert otp.verified_at is not None

    # Inventory
    for item in order.items.select_related("seller_product"):
        inventory = Inventory.objects.get(
            seller_product=item.seller_product
        )

        assert inventory.on_hand == 0
        assert inventory.reserved == 0

    # Commission
    commission = Commission.objects.get(order=order)

    assert commission.store_id == order.store_id
    assert commission.rate == Decimal("7.00")
    assert commission.base_amount == Decimal("250.00")
    assert commission.commission_amount == Decimal("17.50")
    
    
    
@pytest.mark.django_db
def test_delivery_completion_updates_inventory_and_creates_commission(
    delivery_user,
    delivery_assignment,
    order_item,
    inventory,
    commission_rule,
):
    client = APIClient()
    client.force_authenticate(user=delivery_user)

    # Accept assignment
    # Accept assignment
    response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/accept/"
    )
    assert response.status_code == 200

    order = delivery_assignment.order
    order.refresh_from_db()

    # Create OTP
    from apps.orders.services.delivery_otp import DeliveryOTPService

    otp, code = DeliveryOTPService.create(order=order)

    # Complete delivery
    response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/complete/",
        {
            "otp_id": str(otp.id),
            "code": code,
        },
        format="json",
    )

    assert response.status_code == 200

    # Inventory must be sold
    inventory.refresh_from_db()

    assert inventory.on_hand == 0
    assert inventory.reserved == 0

    # Commission must be created
    from apps.finance.models import Commission

    commission = Commission.objects.get(order=order)

    assert commission.store_id == order.store_id
    assert commission.rate == Decimal("7.00")
    assert commission.base_amount == Decimal("250.00")
    assert commission.commission_amount == Decimal("17.50")
    
    
@pytest.mark.django_db
def test_delivery_cannot_complete_order_with_invalid_otp(
    delivery_user,
    delivery_assignment,
    commission_rule,
):
    client = APIClient()
    client.force_authenticate(user=delivery_user)

    # Accept assignment
    response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/accept/"
    )
    assert response.status_code == 200

    order = delivery_assignment.order
    order.refresh_from_db()

    # Create real OTP
    from apps.orders.services.delivery_otp import DeliveryOTPService

    otp, _ = DeliveryOTPService.create(order=order)

    # Try invalid OTP
    response = client.post(
        f"/api/v1/orders/delivery/assignments/{delivery_assignment.id}/complete/",
        {
            "otp_id": str(otp.id),
            "code": "000000",
        },
        format="json",
    )

    assert response.status_code == 400

    order.refresh_from_db()
    otp.refresh_from_db()

    assert order.status == "OUT_FOR_DELIVERY"
    assert otp.status == "ACTIVE"
    assert otp.attempts == 1