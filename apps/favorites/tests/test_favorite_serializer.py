import pytest
from django.contrib.auth import get_user_model

from apps.catalog.models import Category, Product
from apps.favorites.models import Favorite
from apps.favorites.api.serializers import FavoriteSerializer

User = get_user_model()


@pytest.mark.django_db
class TestFavoriteSerializer:

    def setup_method(self):
        self.user = User.objects.create_user(
            phone="01000000000",
            password="TestPassword123",
        )

        self.category = Category.objects.create(
            name="Brakes",
            slug="brakes",
        )

        self.product = Product.objects.create(
            name="Brake Pad",
            slug="brake-pad",
            category=self.category,
        )

        self.favorite = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

    def test_serializes_favorite(self):
        serializer = FavoriteSerializer(self.favorite)

        assert serializer.data["id"] == str(self.favorite.id)
        assert serializer.data["product"] == self.product.id
        assert serializer.data["created_at"] is not None

    def test_product_is_read_only(self):
        serializer = FavoriteSerializer(
            self.favorite,
            data={
                "product": str(self.product.id),
            },
            partial=True,
        )

        assert serializer.is_valid()
        assert "product" not in serializer.validated_data