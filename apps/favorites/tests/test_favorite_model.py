import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.favorites.models import Favorite

from apps.catalog.models import Category, Product
User = get_user_model()


@pytest.mark.django_db
class TestFavoriteModel:

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
            category=self.category,
        )

    def test_favorite_can_be_created(self):
        favorite = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        assert favorite.customer == self.user
        assert favorite.product == self.product

    def test_favorite_has_uuid_primary_key(self):
        favorite = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        assert favorite.id is not None

    def test_favorite_created_at_is_set(self):
        favorite = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        assert favorite.created_at is not None

    def test_same_product_cannot_be_favorited_twice_by_same_customer(self):
        Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        duplicate = Favorite(
            customer=self.user,
            product=self.product,
        )

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_same_product_can_be_favorited_by_different_customers(self):
        first = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        second = Favorite.objects.create(
            customer=self.other_user,
            product=self.product,
        )

        assert first.id != second.id

    def test_customer_can_favorite_different_products(self):
        second_product = Product.objects.create(
        name="Oil Filter",
        slug="oil-filter",
        category=self.category,
    )

        first = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        second = Favorite.objects.create(
            customer=self.user,
            product=second_product,
        )

        assert first.id != second.id

    def test_favorite_str(self):
        favorite = Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        assert str(favorite) == f"{self.user.phone} - {self.product.name}"