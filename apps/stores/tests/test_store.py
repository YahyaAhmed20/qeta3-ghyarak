import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.stores.models import Store, StoreStatus


@pytest.mark.django_db
class TestStoreModel:

    @pytest.fixture
    def seller_owner(self):
        return User.objects.create_user(
            phone="+201001234567",
            role="SELLER_OWNER",
            first_name="Yahya",
            last_name="Seller",
        )

    def test_store_is_created_with_pending_status(self, seller_owner):
        store = Store.objects.create(
            owner=seller_owner,
            name="Yahya Auto Parts",
            slug="yahya-auto-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        assert store.id is not None
        assert store.name == "Yahya Auto Parts"
        assert store.status == StoreStatus.PENDING
        assert store.is_verified is False

    def test_store_can_be_active(self, seller_owner):
        store = Store.objects.create(
            owner=seller_owner,
            name="Suez Auto Parts",
            slug="suez-auto-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
        )

        assert store.status == StoreStatus.ACTIVE

    def test_store_can_be_verified(self, seller_owner):
        store = Store.objects.create(
            owner=seller_owner,
            name="Verified Auto Parts",
            slug="verified-auto-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
            is_verified=True,
        )

        assert store.is_verified is True

    def test_store_rejects_customer_as_owner(self):
        customer = User.objects.create_user(
            phone="+201001234568",
            role="CUSTOMER",
        )

        store = Store(
            owner=customer,
            name="Invalid Store",
            slug="invalid-store",
            phone="+201001234568",
            address="Suez",
            city="Suez",
        )

        with pytest.raises(ValidationError):
            store.full_clean()

    def test_store_allows_admin_as_owner(self):
        admin = User.objects.create_user(
            phone="+201001234569",
            role="ADMIN",
        )

        store = Store(
            owner=admin,
            name="Admin Store",
            slug="admin-store",
            phone="+201001234569",
            address="Suez",
            city="Suez",
        )

        store.full_clean()

    def test_store_str_returns_name(self, seller_owner):
        store = Store.objects.create(
            owner=seller_owner,
            name="Suez Parts",
            slug="suez-parts",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        assert str(store) == "Suez Parts"

    def test_store_coordinates_are_optional(self, seller_owner):
        store = Store.objects.create(
            owner=seller_owner,
            name="No Location Store",
            slug="no-location-store",
            phone="+201001234567",
            address="Suez",
            city="Suez",
        )

        assert store.latitude is None
        assert store.longitude is None