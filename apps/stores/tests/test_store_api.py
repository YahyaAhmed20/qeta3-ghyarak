import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.stores.models import Store, StoreStatus


@pytest.mark.django_db
class TestStoreAPI:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def seller_owner(self):
        return User.objects.create_user(
            phone="+201001234567",
            role="SELLER_OWNER",
        )

    @pytest.fixture
    def customer(self):
        return User.objects.create_user(
            phone="+201001234568",
            role="CUSTOMER",
        )

    def test_authenticated_seller_can_create_store(
        self,
        client,
        seller_owner,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.post(
            "/api/v1/stores/",
            {
                "name": "Alfa Spare Parts",
                "slug": "alfa-spare-parts",
                "description": "Spare parts store",
                "phone": "+201001234567",
                "address": "Suez",
                "city": "Suez",
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["name"] == "Alfa Spare Parts"
        assert response.data["owner"] == seller_owner.id
        assert response.data["status"] == StoreStatus.PENDING
        assert response.data["is_verified"] is False

    def test_unauthenticated_user_cannot_create_store(
        self,
        client,
    ):
        response = client.post(
            "/api/v1/stores/",
            {
                "name": "Test Store",
                "slug": "test-store",
                "phone": "+201001234567",
                "address": "Suez",
                "city": "Suez",
            },
            format="json",
        )

        assert response.status_code == 401

    def test_customer_cannot_create_store(
        self,
        client,
        customer,
    ):
        client.force_authenticate(user=customer)

        response = client.post(
            "/api/v1/stores/",
            {
                "name": "Customer Store",
                "slug": "customer-store",
                "phone": "+201001234567",
                "address": "Suez",
                "city": "Suez",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_seller_can_list_own_stores(
        self,
        client,
        seller_owner,
    ):
        client.force_authenticate(user=seller_owner)

        Store.objects.create(
            owner=seller_owner,
            name="Store One",
            slug="store-one",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        response = client.get("/api/v1/stores/my/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Store One"

    def test_seller_cannot_see_other_sellers_stores(
        self,
        client,
        seller_owner,
    ):
        another_seller = User.objects.create_user(
            phone="+201001234569",
            role="SELLER_OWNER",
        )

        Store.objects.create(
            owner=another_seller,
            name="Other Store",
            slug="other-store",
            phone="+201001234569",
            address="Suez",
            city="Suez",
        )

        client.force_authenticate(user=seller_owner)

        response = client.get(
            "/api/v1/stores/my/",
        )

        assert response.status_code == 200
        assert len(response.data) == 0