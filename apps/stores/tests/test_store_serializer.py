import pytest
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.stores.api.serializers import StoreSerializer
from apps.stores.models import StoreStatus


@pytest.mark.django_db
class TestStoreSerializer:

    @pytest.fixture
    def seller_owner(self):
        return User.objects.create_user(
            phone="+201001234567",
            role="SELLER_OWNER",
        )

    def test_valid_store_data(self, seller_owner):
        serializer = StoreSerializer(
            data={
                "name": "Alfa Spare Parts",
                "slug": "alfa-spare-parts",
                "description": "Spare parts store",
                "phone": "+201001234567",
                "address": "Suez",
                "city": "Suez",
                "latitude": "29.966800",
                "longitude": "32.549800",
            },
            context={
                "request": type(
                    "Request",
                    (),
                    {
                        "user": seller_owner,
                    },
                )(),
            },
        )

        assert serializer.is_valid(), serializer.errors

        store = serializer.save()

        assert store.name == "Alfa Spare Parts"
        assert store.owner == seller_owner
        assert store.status == StoreStatus.PENDING
        assert store.is_verified is False

    def test_owner_is_read_only(self, seller_owner):
        serializer = StoreSerializer(
            data={
                "owner": "some-invalid-owner",
                "name": "Test Store",
                "slug": "test-store",
                "phone": "+201001234567",
                "address": "Suez",
                "city": "Suez",
            },
            context={
                "request": type(
                    "Request",
                    (),
                    {
                        "user": seller_owner,
                    },
                )(),
            },
        )

        assert serializer.is_valid(), serializer.errors

        store = serializer.save()

        assert store.owner == seller_owner

    def test_status_and_verification_are_read_only(self, seller_owner):
        serializer = StoreSerializer(
            data={
                "name": "Test Store",
                "slug": "test-store",
                "phone": "+201001234567",
                "address": "Suez",
                "city": "Suez",
                "status": "ACTIVE",
                "is_verified": True,
            },
            context={
                "request": type(
                    "Request",
                    (),
                    {
                        "user": seller_owner,
                    },
                )(),
            },
        )

        assert serializer.is_valid(), serializer.errors

        store = serializer.save()

        assert store.status == StoreStatus.PENDING
        assert store.is_verified is False

    def test_unauthenticated_request_is_rejected(self):
        request = type(
            "Request",
            (),
            {
                "user": type(
                    "AnonymousUser",
                    (),
                    {
                        "is_authenticated": False,
                    },
                )(),
            },
        )()

        serializer = StoreSerializer(
            data={
                "name": "Test Store",
                "slug": "test-store",
                "phone": "+201001234567",
                "address": "Suez",
                "city": "Suez",
            },
            context={
                "request": request,
            },
        )

        assert serializer.is_valid()

        with pytest.raises(ValidationError):
            serializer.save()