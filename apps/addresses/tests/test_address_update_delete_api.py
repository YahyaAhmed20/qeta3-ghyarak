import pytest
from rest_framework.test import APIClient

from apps.addresses.models import Address


@pytest.mark.django_db
class TestAddressUpdateAPI:

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

    def test_update_address(self, api_client, customer):
        address = self.create_address(
            customer,
            is_default=True,
        )

        api_client.force_authenticate(user=customer)

        response = api_client.patch(
            f"/api/addresses/{address.id}/",
            {
                "label": "Work",
                "city": "Cairo",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["label"] == "Work"
        assert response.data["city"] == "Cairo"

        address.refresh_from_db()

        assert address.label == "Work"
        assert address.city == "Cairo"

    def test_update_can_make_address_default(
        self,
        api_client,
        customer,
    ):
        first = self.create_address(
            customer,
            label="Home",
            is_default=True,
        )

        second = self.create_address(
            customer,
            label="Work",
            is_default=False,
        )

        api_client.force_authenticate(user=customer)

        response = api_client.patch(
            f"/api/addresses/{second.id}/",
            {"is_default": True},
            format="json",
        )

        assert response.status_code == 200

        first.refresh_from_db()
        second.refresh_from_db()

        assert first.is_default is False
        assert second.is_default is True

    def test_cannot_unset_default_address(
        self,
        api_client,
        customer,
    ):
        address = self.create_address(
            customer,
            is_default=True,
        )

        api_client.force_authenticate(user=customer)

        response = api_client.patch(
            f"/api/addresses/{address.id}/",
            {"is_default": False},
            format="json",
        )

        assert response.status_code == 400

        address.refresh_from_db()

        assert address.is_default is True

    def test_cannot_update_another_customer_address(
        self,
        api_client,
        customer,
        another_customer,
    ):
        address = self.create_address(
            another_customer,
            label="Private",
        )

        api_client.force_authenticate(user=customer)

        response = api_client.patch(
            f"/api/addresses/{address.id}/",
            {"label": "Hacked"},
            format="json",
        )

        assert response.status_code == 404

        address.refresh_from_db()

        assert address.label == "Private"

    def test_unauthenticated_user_cannot_update(
        self,
        api_client,
        customer,
    ):
        address = self.create_address(customer)

        response = api_client.patch(
            f"/api/addresses/{address.id}/",
            {"label": "Work"},
            format="json",
        )

        assert response.status_code == 401

    def test_invalid_update_returns_400(
        self,
        api_client,
        customer,
    ):
        address = self.create_address(customer)

        api_client.force_authenticate(user=customer)

        response = api_client.patch(
            f"/api/addresses/{address.id}/",
            {"city": "   "},
            format="json",
        )

        assert response.status_code == 400
        assert "city" in response.data


@pytest.mark.django_db
class TestAddressDeleteAPI:

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

    def test_delete_address(self, api_client, customer):
        address = self.create_address(customer)

        api_client.force_authenticate(user=customer)

        response = api_client.delete(
            f"/api/addresses/{address.id}/",
        )

        assert response.status_code == 204

        assert not Address.objects.filter(
            id=address.id,
        ).exists()

    def test_delete_default_promotes_remaining_address(
        self,
        api_client,
        customer,
    ):
        first = self.create_address(
            customer,
            label="Home",
            is_default=True,
        )

        second = self.create_address(
            customer,
            label="Work",
            is_default=False,
        )

        api_client.force_authenticate(user=customer)

        response = api_client.delete(
            f"/api/addresses/{first.id}/",
        )

        assert response.status_code == 204

        second.refresh_from_db()

        assert second.is_default is True

    def test_cannot_delete_another_customer_address(
        self,
        api_client,
        customer,
        another_customer,
    ):
        address = self.create_address(
            another_customer,
            label="Private",
        )

        api_client.force_authenticate(user=customer)

        response = api_client.delete(
            f"/api/addresses/{address.id}/",
        )

        assert response.status_code == 404

        assert Address.objects.filter(
            id=address.id,
        ).exists()

    def test_delete_nonexistent_address(
        self,
        api_client,
        customer,
    ):
        api_client.force_authenticate(user=customer)

        response = api_client.delete(
            "/api/addresses/00000000-0000-0000-0000-000000000000/",
        )

        assert response.status_code == 404

    def test_unauthenticated_user_cannot_delete(
        self,
        api_client,
        customer,
    ):
        address = self.create_address(customer)

        response = api_client.delete(
            f"/api/addresses/{address.id}/",
        )

        assert response.status_code == 401