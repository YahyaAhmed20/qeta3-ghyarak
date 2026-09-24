from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.stores.models import SellerProduct, Store, StoreStatus
from apps.stores.services.seller_product import SellerProductService

@pytest.mark.django_db
class TestSellerProductService:

    def test_create_seller_product_successfully(
        self,
        active_store,
        active_product,
    ):
        seller_product = (
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("450.00"),
            )
        )

        assert seller_product.store == active_store
        assert seller_product.product == active_product
        assert seller_product.price == Decimal("450.00")
        assert seller_product.sale_price is None

    def test_create_with_sale_price_and_sku(
        self,
        active_store,
        active_product,
    ):
        seller_product = (
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("450.00"),
                sale_price=Decimal("420.00"),
                seller_sku="BOSCH-001",
            )
        )

        assert seller_product.sale_price == Decimal("420.00")
        assert seller_product.seller_sku == "BOSCH-001"

    def test_inactive_store_is_rejected(
        self,
        seller_owner,
        active_product,
    ):
        store = Store.objects.create(
            owner=seller_owner,
            name="Pending Store",
            slug="pending-service-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
            status=StoreStatus.PENDING,
            is_verified=False,
        )

        with pytest.raises(
            ValueError,
            match="Store must be active and verified",
        ):
            SellerProductService.create_seller_product(
                store=store,
                product=active_product,
                price=Decimal("450.00"),
            )

    def test_unverified_store_is_rejected(
        self,
        active_store,
        active_product,
    ):
        active_store.is_verified = False
        active_store.save(update_fields=["is_verified"])

        with pytest.raises(
            ValueError,
            match="Store must be active and verified",
        ):
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("450.00"),
            )

    def test_inactive_product_is_rejected(
        self,
        active_store,
        inactive_product,
    ):
        with pytest.raises(
            ValueError,
            match="Product is not active",
        ):
            SellerProductService.create_seller_product(
                store=active_store,
                product=inactive_product,
                price=Decimal("450.00"),
            )

    def test_duplicate_product_is_rejected(
        self,
        active_store,
        active_product,
    ):
        SellerProductService.create_seller_product(
            store=active_store,
            product=active_product,
            price=Decimal("450.00"),
        )

        with pytest.raises(
            ValueError,
            match="already listed",
        ):
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("430.00"),
            )

    def test_update_seller_product_successfully(
        self,
        active_store,
        active_product,
    ):
        seller_product = (
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("450.00"),
                sale_price=Decimal("420.00"),
                seller_sku="OLD-SKU",
            )
        )

        updated = SellerProductService.update_seller_product(
            seller_product_id=seller_product.id,
            store=active_store,
            price=Decimal("500.00"),
            sale_price=Decimal("470.00"),
            seller_sku="NEW-SKU",
        )

        assert updated.price == Decimal("500.00")
        assert updated.sale_price == Decimal("470.00")
        assert updated.seller_sku == "NEW-SKU"
        assert updated.product == active_product
        assert updated.store == active_store

    def test_update_preserves_unspecified_fields(
        self,
        active_store,
        active_product,
    ):
        seller_product = (
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("450.00"),
                sale_price=Decimal("420.00"),
                seller_sku="BOSCH-001",
            )
        )

        updated = SellerProductService.update_seller_product(
            seller_product_id=seller_product.id,
            store=active_store,
            price=Decimal("500.00"),
        )

        assert updated.price == Decimal("500.00")
        assert updated.sale_price == Decimal("420.00")
        assert updated.seller_sku == "BOSCH-001"

    def test_other_store_cannot_update_seller_product(
        self,
        active_store,
        active_product,
        seller_owner,
    ):
        another_owner = type(seller_owner).objects.create_user(
            phone="+201001234568",
            role="SELLER_OWNER",
        )

        another_store = Store.objects.create(
            owner=another_owner,
            name="Another Store",
            slug="another-update-store",
            phone="+201001234568",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        seller_product = (
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("450.00"),
            )
        )

        with pytest.raises(
            ValueError,
            match="Seller product not found.",
        ):
            SellerProductService.update_seller_product(
                seller_product_id=seller_product.id,
                store=another_store,
                price=Decimal("100.00"),
            )

    def test_update_seller_product_not_found(
        self,
        active_store,
    ):
        import uuid

        with pytest.raises(
            ValueError,
            match="Seller product not found.",
        ):
            SellerProductService.update_seller_product(
                seller_product_id=uuid.uuid4(),
                store=active_store,
                price=Decimal("500.00"),
            )

    def test_update_rejects_invalid_sale_price(
        self,
        active_store,
        active_product,
    ):
        seller_product = (
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("450.00"),
            )
        )

        with pytest.raises(
            ValidationError,
        ):
            SellerProductService.update_seller_product(
                seller_product_id=seller_product.id,
                store=active_store,
                sale_price=Decimal("500.00"),
            )

    def test_unverified_store_cannot_update_seller_product(
        self,
        active_store,
        active_product,
    ):
        seller_product = (
            SellerProductService.create_seller_product(
                store=active_store,
                product=active_product,
                price=Decimal("450.00"),
            )
        )

        active_store.is_verified = False
        active_store.save(update_fields=["is_verified"])

        with pytest.raises(
            ValueError,
            match="Store must be active and verified.",
        ):
            SellerProductService.update_seller_product(
                seller_product_id=seller_product.id,
                store=active_store,
                price=Decimal("500.00"),
            )

    def test_deactivate_seller_product_success(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProductService.create_seller_product(
            store=active_store,
            product=active_product,
            price=1500,
        )

        result = SellerProductService.deactivate_seller_product(
            seller_product_id=seller_product.id,
            store=active_store,
        )

        seller_product.refresh_from_db()

        assert result.id == seller_product.id
        assert seller_product.is_active is False

    def test_deactivate_seller_product_already_inactive(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProductService.create_seller_product(
            store=active_store,
            product=active_product,
            price=1500,
        )

        seller_product.is_active = False
        seller_product.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="already inactive"):
            SellerProductService.deactivate_seller_product(
                seller_product_id=seller_product.id,
                store=active_store,
            )

    def test_activate_seller_product_success(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProductService.create_seller_product(
            store=active_store,
            product=active_product,
            price=1500,
        )

        seller_product.is_active = False
        seller_product.save(update_fields=["is_active"])

        result = SellerProductService.activate_seller_product(
            seller_product_id=seller_product.id,
            store=active_store,
        )

        seller_product.refresh_from_db()

        assert result.id == seller_product.id
        assert seller_product.is_active is True

    def test_activate_seller_product_already_active(
        self,
        active_store,
        active_product,
    ):
        seller_product = SellerProductService.create_seller_product(
            store=active_store,
            product=active_product,
            price=1500,
        )

        with pytest.raises(ValueError, match="already active"):
            SellerProductService.activate_seller_product(
                seller_product_id=seller_product.id,
                store=active_store,
            )