import pytest

from apps.addresses.models import Address
from apps.addresses.services import AddressService


@pytest.mark.django_db
class TestAddressService:

    def test_first_address_becomes_default(self, customer):
        address = AddressService.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Main Street",
        )

        assert address.is_default is True

    def test_second_address_is_not_default_by_default(self, customer):
        first = AddressService.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Main Street",
        )

        second = AddressService.create(
            customer=customer,
            label="Work",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Work Street",
            address_line="Office Street",
        )

        first.refresh_from_db()

        assert first.is_default is True
        assert second.is_default is False

    def test_new_default_replaces_old_default(self, customer):
        first = AddressService.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Home Street",
        )

        second = AddressService.create(
            customer=customer,
            label="Work",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Work Street",
            is_default=True,
        )

        first.refresh_from_db()

        assert first.is_default is False
        assert second.is_default is True

        assert Address.objects.filter(
            customer=customer,
            is_default=True,
        ).count() == 1