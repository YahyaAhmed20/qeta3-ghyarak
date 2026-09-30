import pytest
from django.core.exceptions import ValidationError

from apps.addresses.models import Address


@pytest.mark.django_db
class TestAddressModel:

    def test_create_address(self, customer):
        address = Address.objects.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Main Street",
            building="10",
            floor="3",
            apartment="7",
            landmark="Near the market",
        )

        assert address.pk is not None
        assert address.customer_id == customer.id
        assert address.label == "Home"
        assert address.city == "Suez"
        assert address.is_default is False

    def test_create_address_with_coordinates(self, customer):
        address = Address.objects.create(
            customer=customer,
            label="Work",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Work Street",
            latitude="29.9668",
            longitude="32.5498",
        )

        assert address.latitude == "29.9668"
        assert address.longitude == "32.5498"

    def test_coordinates_are_optional(self, customer):
        address = Address.objects.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Main Street",
        )

        assert address.latitude is None
        assert address.longitude is None

    def test_latitude_cannot_exceed_90(self, customer):
        address = Address(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Main Street",
            latitude="91",
        )

        with pytest.raises(ValidationError):
            address.full_clean()

    def test_longitude_cannot_exceed_180(self, customer):
        address = Address(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Main Street",
            longitude="181",
        )

        with pytest.raises(ValidationError):
            address.full_clean()

    def test_address_belongs_to_customer(
        self,
        customer,
        another_customer,
    ):
        address = Address.objects.create(
            customer=customer,
            label="Home",
            recipient_name="Yahya Ahmed",
            phone="+201001234581",
            city="Suez",
            area="Arbaeen",
            address_line="Main Street",
        )

        assert address.customer_id == customer.id
        assert address.customer_id != another_customer.id