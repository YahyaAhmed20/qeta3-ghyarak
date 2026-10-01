import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification
from apps.notifications.api.serializers import NotificationSerializer


User = get_user_model()


@pytest.mark.django_db
class TestNotificationSerializer:

    def setup_method(self):
        self.user = User.objects.create_user(
            phone="01000000000",
            password="TestPassword123",
        )

        self.notification = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
            data={
                "order_id": "123",
                "order_number": "QTA-20261001-000001",
            },
        )

    def test_serialize_notification(self):
        serializer = NotificationSerializer(self.notification)

        data = serializer.data

        assert data["id"] == str(self.notification.id)
        assert data["type"] == "ORDER_CREATED"
        assert data["title"] == "New Order"
        assert data["message"] == "You have a new order."
        assert data["data"] == {
            "order_id": "123",
            "order_number": "QTA-20261001-000001",
        }
        assert data["is_read"] is False
        assert data["read_at"] is None

    def test_recipient_is_read_only(self):
        serializer = NotificationSerializer(self.notification)

        assert "recipient" not in serializer.fields or (
            serializer.fields["recipient"].read_only is True
        )

    def test_read_only_fields(self):
        serializer = NotificationSerializer(self.notification)

        for field_name in [
            "id",
            "recipient",
            "read_at",
            "created_at",
            "updated_at",
        ]:
            if field_name in serializer.fields:
                assert serializer.fields[field_name].read_only is True

    def test_serializer_contains_expected_fields(self):
        serializer = NotificationSerializer(self.notification)

        expected_fields = {
            "id",
            "recipient",
            "type",
            "title",
            "message",
            "data",
            "is_read",
            "read_at",
            "created_at",
            "updated_at",
        }

        assert set(serializer.fields.keys()) == expected_fields