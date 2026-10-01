import pytest
from django.contrib.auth import get_user_model

from apps.catalog.models import Category, Product
from apps.favorites.models import Favorite
from apps.favorites.selectors.favorite import FavoriteSelector

User = get_user_model()


@pytest.mark.django_db
class TestFavoriteSelector:

    def setup_method(self):
        self.user = User.objects.create_user(
            phone="01000000000",
            password="TestPassword123",
        )

        self.other_user = User.objects.create_user(
            phone="01111111111",
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

        self.second_product = Product.objects.create(
            name="Oil Filter",
            slug="oil-filter",
            category=self.category,
        )

    def test_get_customer_favorites_returns_only_customer_favorites(self):
        favorite = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        Favorite.objects.create(
            customer=self.other_user,
            product=self.second_product,
        )

        favorites = FavoriteSelector.get_customer_favorites(
            customer=self.user,
        )

        assert list(favorites) == [favorite]

    def test_get_favorite_returns_existing_favorite(self):
        favorite = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        result = FavoriteSelector.get_favorite(
            customer=self.user,
            product=self.product,
        )

        assert result == favorite

    def test_get_favorite_returns_none_when_not_found(self):
        result = FavoriteSelector.get_favorite(
            customer=self.user,
            product=self.product,
        )

        assert result is None

    def test_is_favorite_returns_true_when_product_is_favorited(self):
        Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        assert FavoriteSelector.is_favorite(
            customer=self.user,
            product=self.product,
        ) is True

    def test_is_favorite_returns_false_when_product_is_not_favorited(self):
        assert FavoriteSelector.is_favorite(
            customer=self.user,
            product=self.product,
        ) is False