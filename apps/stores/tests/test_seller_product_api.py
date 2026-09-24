from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.stores.models import SellerProduct, Store, StoreStatus


@pytest.mark.django_db
class TestSellerProductCreateAPI:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def seller_owner(self):
        return User.objects.create_user(
            phone="+201001234567",
            role="SELLER_OWNER",
        )

    @pytest.fixture
    def active_store(self, seller_owner):
        return Store.objects.create(
            owner=seller_owner,
            name="Alfa Spare Parts",
            slug="alfa-spare-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

    @pytest.fixture
    def category(self):
        return Category.objects.create(
            name="Filters",
            slug="filters",
        )

    @pytest.fixture
    def brand(self):
        return Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

    @pytest.fixture
    def active_product(self, category, brand):
        return Product.objects.create(
            category=category,
            brand=brand,
            name="Bosch Oil Filter",
            slug="bosch-oil-filter",
            product_type="AFTERMARKET",
            is_active=True,
        )

    def test_create_seller_product_success(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "seller_sku": "BOSCH-001",
                "price": "450.00",
                "sale_price": "400.00",
            },
            format="json",
        )

        assert response.status_code == 201

        assert response.data["store"] == active_store.id
        assert response.data["product"] == active_product.id
        assert response.data["seller_sku"] == "BOSCH-001"
        assert response.data["price"] == "450.00"
        assert response.data["sale_price"] == "400.00"
        assert response.data["is_active"] is True

    def test_create_seller_product_requires_authentication(
        self,
        client,
        active_product,
    ):
        response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "price": "450.00",
            },
            format="json",
        )

        assert response.status_code == 401

    def test_create_seller_product_requires_active_verified_store(
        self,
        client,
        seller_owner,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "price": "450.00",
            },
            format="json",
        )

        assert response.status_code == 400
        assert response.data["detail"] == (
            "You do not have an active verified store."
        )

    def test_create_seller_product_duplicate_is_rejected(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        payload = {
            "product": str(active_product.id),
            "seller_sku": "BOSCH-001",
            "price": "450.00",
        }

        first_response = client.post(
            "/api/v1/stores/products/",
            payload,
            format="json",
        )

        assert first_response.status_code == 201

        second_response = client.post(
            "/api/v1/stores/products/",
            payload,
            format="json",
        )

        assert second_response.status_code == 400
        assert second_response.data["detail"] == (
            "This product is already listed by this store."
        )

    def test_create_seller_product_rejects_zero_price(
        self,
        client,
        seller_owner,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        # Create the store first
        Store.objects.create(
            owner=seller_owner,
            name="Alfa Spare Parts",
            slug="alfa-spare-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "price": "0.00",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_create_seller_product_rejects_sale_price_above_price(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "price": "450.00",
                "sale_price": "500.00",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_create_seller_product_rejects_zero_sale_price(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "price": "450.00",
                "sale_price": "0.00",
            },
            format="json",
        )

        assert response.status_code == 400

    def test_update_seller_product_success(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        create_response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "seller_sku": "BOSCH-001",
                "price": "450.00",
                "sale_price": "400.00",
            },
            format="json",
        )

        assert create_response.status_code == 201

        seller_product_id = create_response.data["id"]

        response = client.patch(
            f"/api/v1/stores/products/{seller_product_id}/",
            {
                "price": "500.00",
                "sale_price": "450.00",
                "seller_sku": "BOSCH-UPDATED",
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["price"] == "500.00"
        assert response.data["sale_price"] == "450.00"
        assert response.data["seller_sku"] == "BOSCH-UPDATED"

        seller_product = SellerProduct.objects.get(
            id=seller_product_id,
        )

        assert seller_product.price == Decimal("500.00")
        assert seller_product.sale_price == Decimal("450.00")
        assert seller_product.seller_sku == "BOSCH-UPDATED"

    def test_update_seller_product_can_remove_sale_price(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        create_response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "price": "450.00",
                "sale_price": "400.00",
            },
            format="json",
        )

        assert create_response.status_code == 201

        seller_product_id = create_response.data["id"]

        response = client.patch(
            f"/api/v1/stores/products/{seller_product_id}/",
            {
                "sale_price": None,
            },
            format="json",
        )

        assert response.status_code == 200
        assert response.data["sale_price"] is None

        seller_product = SellerProduct.objects.get(
            id=seller_product_id,
        )

        assert seller_product.sale_price is None

    def test_update_seller_product_cannot_access_another_store_product(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        create_response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "price": "450.00",
            },
            format="json",
        )

        assert create_response.status_code == 201

        seller_product_id = create_response.data["id"]

        another_owner = User.objects.create_user(
            phone="+201001234568",
            role="SELLER_OWNER",
        )

        Store.objects.create(
            owner=another_owner,
            name="Another Store",
            slug="another-store",
            phone="+201001234568",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        client.force_authenticate(user=another_owner)

        response = client.patch(
            f"/api/v1/stores/products/{seller_product_id}/",
            {
                "price": "999.00",
            },
            format="json",
        )

        assert response.status_code == 404

        seller_product = SellerProduct.objects.get(
            id=seller_product_id,
        )

        assert seller_product.price == Decimal("450.00")

    def test_get_seller_product_success(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        create_response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "seller_sku": "BOSCH-001",
                "price": "450.00",
                "sale_price": "400.00",
            },
            format="json",
        )

        assert create_response.status_code == 201

        seller_product_id = create_response.data["id"]

        response = client.get(
            f"/api/v1/stores/products/{seller_product_id}/"
        )

        assert response.status_code == 200
        assert response.data["id"] == seller_product_id
        assert response.data["product"] == active_product.id
        assert response.data["store"] == active_store.id
        assert response.data["price"] == "450.00"
        assert response.data["sale_price"] == "400.00"
        assert response.data["is_active"] is True

    def test_get_seller_product_cannot_access_another_store_product(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        client.force_authenticate(user=seller_owner)

        create_response = client.post(
            "/api/v1/stores/products/",
            {
                "product": str(active_product.id),
                "price": "450.00",
            },
            format="json",
        )

        assert create_response.status_code == 201

        seller_product_id = create_response.data["id"]

        another_owner = User.objects.create_user(
            phone="+201001234568",
            role="SELLER_OWNER",
        )

        Store.objects.create(
            owner=another_owner,
            name="Another Store",
            slug="another-store",
            phone="+201001234568",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        client.force_authenticate(user=another_owner)

        response = client.get(
            f"/api/v1/stores/products/{seller_product_id}/"
        )

        assert response.status_code == 404

    def test_deactivate_success(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price="250.00",
        )

        client.force_authenticate(user=seller_owner)

        response = client.patch(
            f"/api/v1/stores/products/{seller_product.id}/deactivate/"
        )

        assert response.status_code == 200
        assert response.data["is_active"] is False

        seller_product.refresh_from_db()
        assert seller_product.is_active is False

    def test_activate_success(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price="250.00",
            is_active=False,
        )

        client.force_authenticate(user=seller_owner)

        response = client.patch(
            f"/api/v1/stores/products/{seller_product.id}/activate/"
        )

        assert response.status_code == 200
        assert response.data["is_active"] is True

        seller_product.refresh_from_db()
        assert seller_product.is_active is True

    def test_deactivate_already_inactive_rejected(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price="250.00",
            is_active=False,
        )

        client.force_authenticate(user=seller_owner)

        response = client.patch(
            f"/api/v1/stores/products/{seller_product.id}/deactivate/"
        )

        assert response.status_code == 400
        assert response.data["detail"] == (
            "Seller product is already inactive."
        )

    def test_activate_already_active_rejected(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price="250.00",
            is_active=True,
        )

        client.force_authenticate(user=seller_owner)

        response = client.patch(
            f"/api/v1/stores/products/{seller_product.id}/activate/"
        )

        assert response.status_code == 400
        assert response.data["detail"] == (
            "Seller product is already active."
        )

    def test_list_own_seller_products(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price="250.00",
        )

        client.force_authenticate(user=seller_owner)

        response = client.get("/api/v1/stores/products/")

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["id"] == str(seller_product.id)

    def test_list_does_not_include_other_store_products(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        other_owner = User.objects.create_user(
            phone="+201001234569",
            role="SELLER_OWNER",
        )

        other_store = Store.objects.create(
            owner=other_owner,
            name="Other Store",
            slug="other-store",
            phone="+201001234569",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        SellerProduct.objects.create(
            store=other_store,
            product=active_product,
            price="500.00",
        )

        client.force_authenticate(user=seller_owner)

        response = client.get("/api/v1/stores/products/")

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_list_active_products_filter(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price="250.00",
            is_active=True,
        )

        client.force_authenticate(user=seller_owner)

        response = client.get(
            "/api/v1/stores/products/?is_active=true"
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["is_active"] is True

    def test_list_inactive_products_filter(
        self,
        client,
        seller_owner,
        active_store,
        active_product,
    ):
        SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price="250.00",
            is_active=False,
        )

        client.force_authenticate(user=seller_owner)

        response = client.get(
            "/api/v1/stores/products/?is_active=false"
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["is_active"] is False