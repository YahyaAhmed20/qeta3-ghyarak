import pytest

from apps.cart.api.serializers import CartItemWriteSerializer


@pytest.mark.django_db
class TestCartItemWriteSerializer:

    def test_valid_data(
        self,
        seller_product,
    ):
        serializer = CartItemWriteSerializer(
            data={
                "seller_product_id": str(seller_product.id),
                "quantity": 2,
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data["seller_product_id"] == seller_product.id
        assert serializer.validated_data["quantity"] == 2

    def test_quantity_must_be_positive(
        self,
        seller_product,
    ):
        serializer = CartItemWriteSerializer(
            data={
                "seller_product_id": str(seller_product.id),
                "quantity": 0,
            }
        )

        assert not serializer.is_valid()
        assert "quantity" in serializer.errors

    def test_negative_quantity_is_invalid(
        self,
        seller_product,
    ):
        serializer = CartItemWriteSerializer(
            data={
                "seller_product_id": str(seller_product.id),
                "quantity": -1,
            }
        )

        assert not serializer.is_valid()
        assert "quantity" in serializer.errors

    def test_invalid_seller_product_uuid_is_rejected(self):
        serializer = CartItemWriteSerializer(
            data={
                "seller_product_id": "not-a-uuid",
                "quantity": 1,
            }
        )

        assert not serializer.is_valid()
        assert "seller_product_id" in serializer.errors

    def test_required_fields_are_enforced(self):
        serializer = CartItemWriteSerializer(data={})

        assert not serializer.is_valid()
        assert "seller_product_id" in serializer.errors
        assert "quantity" in serializer.errors

    def test_client_cannot_submit_price_fields(
        self,
        seller_product,
    ):
        serializer = CartItemWriteSerializer(
            data={
                "seller_product_id": str(seller_product.id),
                "quantity": 2,
                "unit_price": "1.00",
                "subtotal": "1.00",
            }
        )

        assert serializer.is_valid()

        assert "unit_price" not in serializer.validated_data
        assert "subtotal" not in serializer.validated_data