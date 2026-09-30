import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError

from apps.addresses.models import Address
from apps.addresses.services import AddressService


@pytest.mark.django_db
class TestAddressServiceUpdate:

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

    def test_update_address(self, customer):
        address = self.create_address(customer)

        updated = AddressService.update(
            address=address,
            label="Work",
            city="Cairo",
            area="Nasr City",
            address_line="New Street",
        )

        address.refresh_from_db()

        assert updated.id == address.id
        assert address.label == "Work"
        assert address.city == "Cairo"
        assert address.area == "Nasr City"
        assert address.address_line == "New Street"

    def test_update_strips_text_fields(self, customer):
        address = self.create_address(customer)

        AddressService.update(
            address=address,
            label="  Work  ",
            city="  Suez  ",
            area="  Arbaeen  ",
            address_line="  New Street  ",
        )

        address.refresh_from_db()

        assert address.label == "Work"
        assert address.city == "Suez"
        assert address.area == "Arbaeen"
        assert address.address_line == "New Street"

    def test_update_to_default_replaces_old_default(self, customer):
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

        AddressService.update(
            address=second,
            is_default=True,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        assert first.is_default is False
        assert second.is_default is True

        assert Address.objects.filter(
            customer=customer,
            is_default=True,
        ).count() == 1

    def test_cannot_unset_default_address(self, customer):
        address = self.create_address(
            customer,
            is_default=True,
        )

        with pytest.raises(ValueError):
            AddressService.update(
                address=address,
                is_default=False,
            )

        address.refresh_from_db()

        assert address.is_default is True

    def test_update_coordinates(self, customer):
        address = self.create_address(customer)

        AddressService.update(
            address=address,
            latitude="29.966800",
            longitude="32.549800",
        )

        address.refresh_from_db()

        assert address.latitude == Decimal("29.966800")
        assert address.longitude == Decimal("32.549800")

    def test_invalid_coordinates_are_rejected(self, customer):
        address = self.create_address(customer)

        with pytest.raises(ValidationError):
            AddressService.update(
                address=address,
                latitude="91",
            )


@pytest.mark.django_db
class TestAddressServiceDelete:

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

    def test_delete_address(self, customer):
        address = self.create_address(customer)

        AddressService.delete(address=address)

        assert not Address.objects.filter(
            id=address.id,
        ).exists()

    def test_delete_default_promotes_latest_remaining_address(
        self,
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

        AddressService.delete(address=first)

        second.refresh_from_db()

        assert not Address.objects.filter(
            id=first.id,
        ).exists()

        assert second.is_default is True

    def test_delete_non_default_does_not_change_default(
        self,
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

        AddressService.delete(address=second)

        first.refresh_from_db()

        assert first.is_default is True
        assert Address.objects.filter(
            customer=customer,
            is_default=True,
        ).count() == 1