import pytest

from apps.catalog.models import Category, Product
from apps.favorites.models import Favorite
from apps.favorites.services.favorite import FavoriteService
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestFavoriteService:

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

    def test_add_favorite_creates_favorite(self):
        favorite = FavoriteService.add_favorite(
            customer=self.user,
            product=self.product,
        )

        assert favorite.customer == self.user
        assert favorite.product == self.product

    def test_add_same_favorite_returns_existing_favorite(self):
        first = FavoriteService.add_favorite(
            customer=self.user,
            product=self.product,
        )

        second = FavoriteService.add_favorite(
            customer=self.user,
            product=self.product,
        )

        assert first.id == second.id
        assert Favorite.objects.count() == 1

    def test_remove_favorite_deletes_favorite(self):
        Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        result = FavoriteService.remove_favorite(
            customer=self.user,
            product=self.product,
        )

        assert result is True
        assert not Favorite.objects.filter(
            customer=self.user,
            product=self.product,
        ).exists()

    def test_remove_non_existing_favorite_returns_false(self):
        result = FavoriteService.remove_favorite(
            customer=self.user,
            product=self.product,
        )

        assert result is False