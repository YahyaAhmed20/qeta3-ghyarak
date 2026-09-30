import pytest
from rest_framework.test import APIClient

from apps.addresses.models import Address
from apps.accounts.models import User


@pytest.mark.django_db
class TestAddressCreateAPI:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_create_address(self, api_client, customer):
        api_client.force_authenticate(user=customer)

        response = api_client.post(
            "/api/addresses/",
            {
                "label": "Home",
                "recipient_name": "Yahya Ahmed",
                "phone": "+201001234581",
                "city": "Suez",
                "area": "Arbaeen",
                "address_line": "Main Street",
                "building": "10",
                "floor": "3",
                "apartment": "7",
                "landmark": "Near the market",
                "latitude": "29.966800",
                "longitude": "32.549800",
                "is_default": False,
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["label"] == "Home"
        assert response.data["city"] == "Suez"

        address = Address.objects.get(
            customer=customer,
        )

        assert address.recipient_name == "Yahya Ahmed"
        assert address.is_default is True

    def test_customer_cannot_be_changed_from_request(
        self,
        api_client,
        customer,
        another_customer,
    ):
        api_client.force_authenticate(user=customer)

        response = api_client.post(
            "/api/addresses/",
            {
                "label": "Home",
                "recipient_name": "Yahya Ahmed",
                "phone": "+201001234581",
                "city": "Suez",
                "area": "Arbaeen",
                "address_line": "Main Street",
                "customer": str(another_customer.id),
            },
            format="json",
        )

        assert response.status_code == 201

        address = Address.objects.get()

        assert address.customer_id == customer.id
        assert address.customer_id != another_customer.id

    def test_unauthenticated_user_cannot_create_address(
        self,
        api_client,
    ):
        response = api_client.post(
            "/api/addresses/",
            {
                "label": "Home",
                "recipient_name": "Yahya Ahmed",
                "phone": "+201001234581",
                "city": "Suez",
                "area": "Arbaeen",
                "address_line": "Main Street",
            },
            format="json",
        )

        assert response.status_code == 401

    def test_invalid_data_returns_400(
        self,
        api_client,
        customer,
    ):
        api_client.force_authenticate(user=customer)

        response = api_client.post(
            "/api/addresses/",
            {
                "label": "   ",
                "recipient_name": "Yahya Ahmed",
                "phone": "+201001234581",
                "city": "Suez",
                "area": "Arbaeen",
                "address_line": "Main Street",
            },
            format="json",
        )

        assert response.status_code == 400
        assert "label" in response.data

    def test_create_default_address(
        self,
        api_client,
        customer,
    ):
        api_client.force_authenticate(user=customer)

        response = api_client.post(
            "/api/addresses/",
            {
                "label": "Home",
                "recipient_name": "Yahya Ahmed",
                "phone": "+201001234581",
                "city": "Suez",
                "area": "Arbaeen",
                "address_line": "Main Street",
                "is_default": True,
            },
            format="json",
        )

        assert response.status_code == 201

        address = Address.objects.get(
            customer=customer,
        )

        assert address.is_default is True