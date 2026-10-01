import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product
from apps.favorites.models import Favorite

User = get_user_model()


@pytest.mark.django_db
class TestFavoriteAPI:

    def setup_method(self):
        self.client = APIClient()

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

        self.client.force_authenticate(user=self.user)

    def test_add_favorite(self):
        response = self.client.post(
            "/api/favorites/",
            {
                "product": str(self.product.id),
            },
            format="json",
        )

        assert response.status_code == 201
        assert Favorite.objects.filter(
            customer=self.user,
            product=self.product,
        ).exists()

    def test_add_same_favorite_is_idempotent(self):
        first = self.client.post(
            "/api/favorites/",
            {"product": str(self.product.id)},
            format="json",
        )

        second = self.client.post(
            "/api/favorites/",
            {"product": str(self.product.id)},
            format="json",
        )

        assert first.status_code == 201
        assert second.status_code == 200
        assert Favorite.objects.filter(
            customer=self.user,
            product=self.product,
        ).count() == 1

    def test_list_favorites(self):
        Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )
        Favorite.objects.create(
            customer=self.user,
            product=self.second_product,
        )

        response = self.client.get("/api/favorites/")

        assert response.status_code == 200
        assert len(response.data) == 2

    def test_delete_favorite(self):
        Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        response = self.client.delete(
            f"/api/favorites/{self.product.id}/"
        )

        assert response.status_code == 204
        assert not Favorite.objects.filter(
            customer=self.user,
            product=self.product,
        ).exists()

    def test_delete_non_existing_favorite(self):
        response = self.client.delete(
            f"/api/favorites/{self.product.id}/"
        )

        assert response.status_code == 404

    def test_check_favorite_returns_true(self):
        Favorite.objects.create(
            customer=self.user,
            product=self.product,
        )

        response = self.client.get(
            f"/api/favorites/check/{self.product.id}/"
        )

        assert response.status_code == 200
        assert response.data["is_favorite"] is True

    def test_check_favorite_returns_false(self):
        response = self.client.get(
            f"/api/favorites/check/{self.product.id}/"
        )

        assert response.status_code == 200
        assert response.data["is_favorite"] is False

    def test_customer_cannot_delete_another_customer_favorite(self):
        Favorite.objects.create(
            customer=self.other_user,
            product=self.product,
        )

        response = self.client.delete(
            f"/api/favorites/{self.product.id}/"
        )

        assert response.status_code == 404
        assert Favorite.objects.filter(
            customer=self.other_user,
            product=self.product,
        ).exists()

    def test_unauthenticated_user_cannot_access_favorites(self):
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/favorites/")

        assert response.status_code == 401