import pytest

from apps.addresses.api.serializers import (
    AddressCreateSerializer,
    AddressUpdateSerializer,
)


@pytest.mark.django_db
class TestAddressCreateSerializer:

    def get_valid_data(self):
        return {
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
        }

    def test_valid_data(self):
        data = self.get_valid_data()

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_customer_is_not_allowed_as_input(self):
        data = self.get_valid_data()
        data["customer"] = "some-customer-id"

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        assert "customer" not in serializer.validated_data

    def test_empty_label_is_invalid(self):
        data = self.get_valid_data()
        data["label"] = "   "

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid() is False
        assert "label" in serializer.errors

    def test_empty_recipient_name_is_invalid(self):
        data = self.get_valid_data()
        data["recipient_name"] = "   "

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid() is False
        assert "recipient_name" in serializer.errors

    def test_empty_phone_is_invalid(self):
        data = self.get_valid_data()
        data["phone"] = "   "

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid() is False
        assert "phone" in serializer.errors

    def test_empty_city_is_invalid(self):
        data = self.get_valid_data()
        data["city"] = "   "

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid() is False
        assert "city" in serializer.errors

    def test_empty_area_is_invalid(self):
        data = self.get_valid_data()
        data["area"] = "   "

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid() is False
        assert "area" in serializer.errors

    def test_empty_address_line_is_invalid(self):
        data = self.get_valid_data()
        data["address_line"] = "   "

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid() is False
        assert "address_line" in serializer.errors

    def test_optional_fields_can_be_omitted(self):
        data = {
            "label": "Home",
            "recipient_name": "Yahya Ahmed",
            "phone": "+201001234581",
            "city": "Suez",
            "area": "Arbaeen",
            "address_line": "Main Street",
        }

        serializer = AddressCreateSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_update_serializer_accepts_partial_data(self):
        serializer = AddressUpdateSerializer(
            data={"city": "Cairo"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors

    def test_update_serializer_rejects_empty_city(self):
        serializer = AddressUpdateSerializer(
            data={"city": "   "},
            partial=True,
        )

        assert serializer.is_valid() is False
        assert "city" in serializer.errors