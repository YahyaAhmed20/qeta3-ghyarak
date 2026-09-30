import pytest

from apps.addresses.models import Address
from apps.addresses.selectors import AddressSelector


@pytest.mark.django_db
class TestAddressSelector:

    def test_get_address(self, customer):
        address = Address.objects.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Main Street",
        )

        result = AddressSelector.get_address(
            address_id=address.id,
        )

        assert result is not None
        assert result.id == address.id
        assert result.customer_id == customer.id

    def test_get_address_returns_none_for_invalid_id(self):
        result = AddressSelector.get_address(
            address_id="00000000-0000-0000-0000-000000000000",
        )

        assert result is None

    def test_get_customer_addresses(self, customer):
        first = Address.objects.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Home Street",
            is_default=True,
        )

        second = Address.objects.create(
            customer=customer,
            label="Work",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Work Street",
        )

        results = list(
            AddressSelector.get_customer_addresses(
                customer_id=customer.id,
            )
        )

        assert len(results) == 2
        assert results[0].id == first.id
        assert results[1].id == second.id

    def test_get_customer_addresses_does_not_return_other_customers(
        self,
        customer,
        another_customer,
    ):
        Address.objects.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Home Street",
        )

        Address.objects.create(
            customer=another_customer,
            label="Home",
            recipient_name="Another Customer",
            phone="+201001234582",
            city="Suez",
            area="Arbaeen",
            address_line="Other Street",
        )

        results = list(
            AddressSelector.get_customer_addresses(
                customer_id=customer.id,
            )
        )

        assert len(results) == 1
        assert results[0].customer_id == customer.id

    def test_get_default_address(self, customer):
        address = Address.objects.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Home Street",
            is_default=True,
        )

        result = AddressSelector.get_default_address(
            customer_id=customer.id,
        )

        assert result is not None
        assert result.id == address.id

    def test_get_default_address_returns_none_when_not_exists(
        self,
        customer,
    ):
        Address.objects.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Home Street",
        )

        result = AddressSelector.get_default_address(
            customer_id=customer.id,
        )

        assert result is None