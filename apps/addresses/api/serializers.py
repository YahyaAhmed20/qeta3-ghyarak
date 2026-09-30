from rest_framework import serializers

from apps.addresses.models import Address


class AddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "label",
            "recipient_name",
            "phone",
            "city",
            "area",
            "address_line",
            "building",
            "floor",
            "apartment",
            "landmark",
            "latitude",
            "longitude",
            "is_default",
        ]

    def validate_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Address label cannot be empty."
            )
        return value

    def validate_recipient_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Recipient name cannot be empty."
            )
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Phone cannot be empty."
            )
        return value

    def validate_city(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "City cannot be empty."
            )
        return value

    def validate_area(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Area cannot be empty."
            )
        return value

    def validate_address_line(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Address line cannot be empty."
            )
        return value


class AddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "label",
            "recipient_name",
            "phone",
            "city",
            "area",
            "address_line",
            "building",
            "floor",
            "apartment",
            "landmark",
            "latitude",
            "longitude",
            "is_default",
        ]

    def validate_label(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Address label cannot be empty."
            )

        return value

    def validate_recipient_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Recipient name cannot be empty."
            )

        return value

    def validate_phone(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Phone cannot be empty."
            )

        return value

    def validate_city(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "City cannot be empty."
            )

        return value

    def validate_area(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Area cannot be empty."
            )

        return value

    def validate_address_line(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Address line cannot be empty."
            )

        return value


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "recipient_name",
            "phone",
            "city",
            "area",
            "address_line",
            "building",
            "floor",
            "apartment",
            "landmark",
            "latitude",
            "longitude",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]