from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.catalog.models import Brand, Category, Product
from apps.stores.api.serializers import SellerProductSerializer
from apps.stores.models import SellerProduct, Store, StoreStatus
from apps.stores.services.seller_product import SellerProductService


@pytest.mark.django_db
class TestSellerProduct:

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

    def test_create_seller_product(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            seller_sku="BOSCH-001",
            price=Decimal("450.00"),
        )

        seller_product.full_clean()

        assert seller_product.store == active_store
        assert seller_product.product == active_product
        assert seller_product.price == Decimal("450.00")
        assert seller_product.sale_price is None
        assert seller_product.is_active is True

    def test_sale_price_is_optional(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
        )

        seller_product.full_clean()

        assert seller_product.sale_price is None

    def test_sale_price_cannot_exceed_price(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
            sale_price=Decimal("500.00"),
        )

        with pytest.raises(ValidationError):
            seller_product.full_clean()

    def test_price_must_be_positive(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct(
            store=active_store,
            product=active_product,
            price=Decimal("0.00"),
        )

        with pytest.raises(ValidationError):
            seller_product.full_clean()

    def test_sale_price_must_be_positive(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
            sale_price=Decimal("0.00"),
        )

        with pytest.raises(ValidationError):
            seller_product.full_clean()

    def test_inactive_store_is_rejected(
        self,
        seller_owner,
        active_product,
    ):
        store = Store.objects.create(
            owner=seller_owner,
            name="Pending Store",
            slug="pending-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
            status=StoreStatus.PENDING,
        )

        seller_product = SellerProduct(
            store=store,
            product=active_product,
            price=Decimal("450.00"),
        )

        with pytest.raises(
            ValidationError,
            match="Store must be active",
        ):
            seller_product.full_clean()

    def test_inactive_product_is_rejected(
        self,
        active_store,
        category,
        brand,
    ):
        product = Product.objects.create(
            category=category,
            brand=brand,
            name="Inactive Filter",
            slug="inactive-filter",
            product_type="AFTERMARKET",
            is_active=False,
        )

        seller_product = SellerProduct(
            store=active_store,
            product=product,
            price=Decimal("450.00"),
        )

        with pytest.raises(
            ValidationError,
            match="Product must be active",
        ):
            seller_product.full_clean()

    def test_same_product_cannot_be_added_twice_to_same_store(
        self,
        active_store,
        active_product,
    ):
        SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
        )

        duplicate = SellerProduct(
            store=active_store,
            product=active_product,
            price=Decimal("430.00"),
        )

        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_same_product_can_be_sold_by_different_stores(
        self,
        seller_owner,
        active_store,
        active_product,
    ):
        another_owner = User.objects.create_user(
            phone="+201001234568",
            role="SELLER_OWNER",
        )

        another_store = Store.objects.create(
            owner=another_owner,
            name="Another Store",
            slug="another-store",
            phone="+201001234568",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        first = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
        )

        second = SellerProduct.objects.create(
            store=another_store,
            product=active_product,
            price=Decimal("430.00"),
        )

        assert first.product == second.product
        assert first.store != second.store

    def test_str_returns_store_and_product_name(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProduct.objects.create(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
        )

        assert str(seller_product) == (
            "Alfa Spare Parts - Bosch Oil Filter"
        )

    def test_serializer_output(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProductService.create_seller_product(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
            sale_price=Decimal("400.00"),
            seller_sku="BOSCH-001",
        )

        serializer = SellerProductSerializer(seller_product)

        assert serializer.data["id"] == str(seller_product.id)
        assert serializer.data["store"] == active_store.id
        assert serializer.data["product"] == active_product.id
        assert serializer.data["seller_sku"] == "BOSCH-001"
        assert serializer.data["price"] == "450.00"
        assert serializer.data["sale_price"] == "400.00"
        assert serializer.data["is_active"] is True

    def test_serializer_read_only_fields(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProductService.create_seller_product(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
        )

        serializer = SellerProductSerializer(seller_product)

        assert serializer.fields["store"].read_only is True
        assert serializer.fields["is_active"].read_only
        assert serializer.fields["created_at"].read_only
        assert serializer.fields["updated_at"].read_only