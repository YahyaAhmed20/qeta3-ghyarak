import pytest
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.accounts.models import User
from apps.stores.models import Store, StoreStatus
from apps.stores.services.store import StoreService


@pytest.mark.django_db
class TestStoreService:

    @pytest.fixture
    def seller_owner(self):
        return User.objects.create_user(
            phone="+201001234567",
            role="SELLER_OWNER",
            first_name="Yahya",
            last_name="Seller",
        )

    @pytest.fixture
    def customer(self):
        return User.objects.create_user(
            phone="+201001234568",
            role="CUSTOMER",
        )

    def test_create_store_successfully(self, seller_owner):
        store = StoreService.create_store(
            owner=seller_owner,
            name="Yahya Auto Parts",
            slug="yahya-auto-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        assert store.id is not None
        assert store.owner == seller_owner
        assert store.name == "Yahya Auto Parts"
        assert store.status == StoreStatus.PENDING
        assert store.is_verified is False

    def test_create_store_with_optional_fields(self, seller_owner):
        store = StoreService.create_store(
            owner=seller_owner,
            name="Suez Auto Parts",
            slug="suez-auto-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
            description="Automotive spare parts.",
            latitude="29.9668",
            longitude="32.5498",
        )

        assert store.description == "Automotive spare parts."
        assert store.latitude == Decimal("29.9668")
        assert store.longitude == Decimal("32.5498")

    def test_customer_cannot_create_store(self, customer):
        with pytest.raises(ValueError, match="Only seller owners"):
            StoreService.create_store(
                owner=customer,
                name="Invalid Store",
                slug="invalid-store",
                phone="+201001234568",
                address="Suez",
                city="Suez",
            )

        assert Store.objects.count() == 0

    def test_admin_can_create_store(self):
        admin = User.objects.create_user(
            phone="+201001234569",
            role="ADMIN",
        )

        store = StoreService.create_store(
            owner=admin,
            name="Admin Store",
            slug="admin-store",
            phone="+201001234569",
            address="Suez",
            city="Suez",
        )

        assert store.owner == admin
        assert store.status == StoreStatus.PENDING

    def test_super_admin_can_create_store(self):
        admin = User.objects.create_user(
            phone="+201001234570",
            role="SUPER_ADMIN",
        )

        store = StoreService.create_store(
            owner=admin,
            name="Super Admin Store",
            slug="super-admin-store",
            phone="+201001234570",
            address="Suez",
            city="Suez",
        )

        assert store.owner == admin

    def test_invalid_store_data_is_rejected(self, seller_owner):
        with pytest.raises(ValidationError):
            StoreService.create_store(
                owner=seller_owner,
                name="Invalid Store",
                slug="invalid-store",
                phone="+201001234567",
                address="Suez",
                city="Suez",
                latitude="999999",
            )

        assert Store.objects.count() == 0

    def test_approve_pending_store(self, seller_owner):
        store = StoreService.create_store(
            owner=seller_owner,
            name="Pending Store",
            slug="pending-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        approved_store = StoreService.approve_store(
            store_id=store.id,
        )

        assert approved_store.status == StoreStatus.ACTIVE
        assert approved_store.is_verified is True

    def test_approve_store_not_found(self):
        import uuid

        with pytest.raises(
            ValueError,
            match="Store not found.",
        ):
            StoreService.approve_store(
                store_id=uuid.uuid4(),
            )

    def test_only_pending_store_can_be_approved(
        self,
        seller_owner,
    ):
        store = StoreService.create_store(
            owner=seller_owner,
            name="Active Store",
            slug="active-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        store.status = StoreStatus.ACTIVE
        store.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Only pending stores",
        ):
            StoreService.approve_store(
                store_id=store.id,
            )

    def test_approve_store_is_atomic(
        self,
        seller_owner,
    ):
        store = StoreService.create_store(
            owner=seller_owner,
            name="Atomic Store",
            slug="atomic-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        StoreService.approve_store(
            store_id=store.id,
        )

        store.refresh_from_db()

        assert store.status == StoreStatus.ACTIVE
        assert store.is_verified is True

    def test_update_store_successfully(self, seller_owner):
        store = StoreService.create_store(
            owner=seller_owner,
            name="Old Store Name",
            slug="old-store-name",
            phone="+201001234567",
            address="Old Address",
            city="Suez",
        )

        updated_store = StoreService.update_store(
            store_id=store.id,
            owner=seller_owner,
            name="New Store Name",
            phone="+201009876543",
            address="New Address",
        )

        assert updated_store.name == "New Store Name"
        assert updated_store.phone == "+201009876543"
        assert updated_store.address == "New Address"
        assert updated_store.city == "Suez"
        assert updated_store.slug == "old-store-name"

    def test_update_store_cannot_be_done_by_another_owner(
        self,
        seller_owner,
    ):
        another_seller = User.objects.create_user(
            phone="+201001234568",
            role="SELLER_OWNER",
        )

        store = StoreService.create_store(
            owner=seller_owner,
            name="My Store",
            slug="my-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        with pytest.raises(
            ValueError,
            match="Store not found.",
        ):
            StoreService.update_store(
                store_id=store.id,
                owner=another_seller,
                name="Hacked Store",
            )

    def test_update_store_not_found(self, seller_owner):
        import uuid

        with pytest.raises(
            ValueError,
            match="Store not found.",
        ):
            StoreService.update_store(
                store_id=uuid.uuid4(),
                owner=seller_owner,
                name="Test",
            )

    def test_suspended_store_cannot_be_updated(
        self,
        seller_owner,
    ):
        store = StoreService.create_store(
            owner=seller_owner,
            name="Suspended Store",
            slug="suspended-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        store.status = StoreStatus.SUSPENDED
        store.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Suspended stores cannot be updated.",
        ):
            StoreService.update_store(
                store_id=store.id,
                owner=seller_owner,
                name="Updated Name",
            )

    def test_update_store_preserves_unspecified_fields(
        self,
        seller_owner,
    ):
        store = StoreService.create_store(
            owner=seller_owner,
            name="Original Store",
            slug="original-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
            description="Original description",
        )

        updated_store = StoreService.update_store(
            store_id=store.id,
            owner=seller_owner,
            name="Updated Store",
        )

        assert updated_store.name == "Updated Store"
        assert updated_store.slug == "original-store"
        assert updated_store.phone == "+201001234567"
        assert updated_store.address == "Suez"
        assert updated_store.city == "Suez"
        assert updated_store.description == "Original description"