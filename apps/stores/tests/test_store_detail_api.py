import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.stores.models import Store


@pytest.mark.django_db
class TestStoreDetailAPI:

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
            name="Alfa Spare Parts",
            slug="alfa-spare-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

    def test_owner_can_retrieve_own_store(
        self,
        client,
        seller_owner,
        store,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.get(
            f"/api/v1/stores/{store.id}/",
        )

        assert response.status_code == 200
        assert response.data["id"] == str(store.id)
        assert response.data["name"] == "Alfa Spare Parts"

    def test_other_seller_cannot_retrieve_store(
        self,
        client,
        another_seller,
        store,
    ):
        client.force_authenticate(user=another_seller)

        response = client.get(
            f"/api/v1/stores/{store.id}/",
        )

        assert response.status_code == 404

    def test_customer_cannot_retrieve_store(
        self,
        client,
        customer,
        store,
    ):
        client.force_authenticate(user=customer)

        response = client.get(
            f"/api/v1/stores/{store.id}/",
        )

        assert response.status_code == 404

    def test_unauthenticated_user_cannot_retrieve_store(
        self,
        client,
        store,
    ):
        response = client.get(
            f"/api/v1/stores/{store.id}/",
        )

        assert response.status_code == 401

    def test_nonexistent_store_returns_404(
        self,
        client,
        seller_owner,
    ):
        import uuid

        client.force_authenticate(user=seller_owner)

        response = client.get(
            f"/api/v1/stores/{uuid.uuid4()}/",
        )

        assert response.status_code == 404