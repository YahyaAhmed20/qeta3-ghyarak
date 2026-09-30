import pytest
from rest_framework.test import APIClient

from apps.addresses.models import Address


@pytest.mark.django_db
class TestAddressListAPI:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def create_address(self, customer, **kwargs):
        defaults = {
            "label": "Home",
            "recipient_name": "Yahya Ahmed",
            "phone": "+201001234581",
            "city": "Suez",
            "area": "Arbaeen",
            "address_line": "Main Street",
        }
        defaults.update(kwargs)

        return Address.objects.create(
            customer=customer,
            **defaults,
        )

    def test_list_returns_customer_addresses_only(
        self,
        api_client,
        customer,
        another_customer,
    ):
        own_address = self.create_address(
            customer,
            is_default=True,
        )

        self.create_address(
            another_customer,
            label="Other Customer",
        )

        api_client.force_authenticate(user=customer)

        response = api_client.get("/api/addresses/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(own_address.id)

    def test_list_orders_default_first(
        self,
        api_client,
        customer,
    ):
        default_address = self.create_address(
            customer,
            label="Home",
            is_default=True,
        )

        normal_address = self.create_address(
            customer,
            label="Work",
            is_default=False,
        )

        api_client.force_authenticate(user=customer)

        response = api_client.get("/api/addresses/")

        assert response.status_code == 200
        assert response.data[0]["id"] == str(default_address.id)
        assert response.data[1]["id"] == str(normal_address.id)

    def test_unauthenticated_user_cannot_list_addresses(
        self,
        api_client,
    ):
        response = api_client.get("/api/addresses/")

        assert response.status_code == 401


@pytest.mark.django_db
class TestAddressDetailAPI:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def create_address(self, customer, **kwargs):
        defaults = {
            "label": "Home",
            "recipient_name": "Yahya Ahmed",
            "phone": "+201001234581",
            "city": "Suez",
            "area": "Arbaeen",
            "address_line": "Main Street",
        }
        defaults.update(kwargs)

        return Address.objects.create(
            customer=customer,
            **defaults,
        )

    def test_get_address(
        self,
        api_client,
        customer,
    ):
        address = self.create_address(
            customer,
            is_default=True,
        )

        api_client.force_authenticate(user=customer)

        response = api_client.get(
            f"/api/addresses/{address.id}/",
        )

        assert response.status_code == 200
        assert response.data["id"] == str(address.id)
        assert response.data["label"] == "Home"
        assert response.data["city"] == "Suez"

    def test_customer_cannot_access_another_customer_address(
        self,
        api_client,
        customer,
        another_customer,
    ):
        address = self.create_address(
            another_customer,
            label="Private Address",
        )

        api_client.force_authenticate(user=customer)

        response = api_client.get(
            f"/api/addresses/{address.id}/",
        )

        assert response.status_code == 404

    def test_nonexistent_address_returns_404(
        self,
        api_client,
        customer,
    ):
        api_client.force_authenticate(user=customer)

        response = api_client.get(
            "/api/addresses/00000000-0000-0000-0000-000000000000/",
        )

        assert response.status_code == 404

    def test_unauthenticated_user_cannot_get_address(
        self,
        api_client,
        customer,
    ):
        address = self.create_address(customer)

        response = api_client.get(
            f"/api/addresses/{address.id}/",
        )

        assert response.status_code == 401