import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.stores.models import Store


@pytest.mark.django_db
class TestStoreUpdateAPI:

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
    def another_seller(self):
        return User.objects.create_user(
            phone="+201001234568",
            role="SELLER_OWNER",
        )

    @pytest.fixture
    def customer(self):
        return User.objects.create_user(
            phone="+201001234569",
            role="CUSTOMER",
        )

    @pytest.fixture
    def store(self, seller_owner):
        return Store.objects.create(
            owner=seller_owner,
            name="Original Store",
            slug="original-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

    def test_owner_can_update_store(
        self,
        client,
        seller_owner,
        store,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.patch(
            f"/api/v1/stores/{store.id}/",
            {
                "name": "Updated Store",
                "phone": "+201009876543",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["name"] == "Updated Store"
        assert response.data["phone"] == "+201009876543"
        assert response.data["address"] == "Suez"

    def test_other_seller_cannot_update_store(
        self,
        client,
        another_seller,
        store,
    ):
        client.force_authenticate(user=another_seller)

        response = client.patch(
            f"/api/v1/stores/{store.id}/",
            {
                "name": "Unauthorized Update",
            },
            format="json",
        )

        assert response.status_code == 404

    def test_customer_cannot_update_store(
        self,
        client,
        customer,
        store,
    ):
        client.force_authenticate(user=customer)

        response = client.patch(
            f"/api/v1/stores/{store.id}/",
            {
                "name": "Unauthorized Update",
            },
            format="json",
        )

        assert response.status_code == 404

    def test_unauthenticated_user_cannot_update_store(
        self,
        client,
        store,
    ):
        response = client.patch(
            f"/api/v1/stores/{store.id}/",
            {
                "name": "Unauthorized Update",
            },
            format="json",
        )

        assert response.status_code == 401

    def test_partial_update_preserves_other_fields(
        self,
        client,
        seller_owner,
        store,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.patch(
            f"/api/v1/stores/{store.id}/",
            {
                "name": "New Name",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["name"] == "New Name"
        assert response.data["slug"] == "original-store"
        assert response.data["phone"] == "+201001234567"
        assert response.data["city"] == "Suez"