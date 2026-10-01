import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.notifications.models import Notification


User = get_user_model()


@pytest.mark.django_db
class TestNotificationModel:

    def setup_method(self):
        self.user = User.objects.create_user(
            phone="01000000000",
            password="TestPassword123",
        )

    def test_create_notification(self):
        notification = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
        )

        assert notification.id is not None
        assert notification.recipient == self.user
        assert notification.type == Notification.NotificationType.ORDER_CREATED
        assert notification.title == "New Order"
        assert notification.message == "You have a new order."

    def test_default_values(self):
        notification = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
        )

        assert notification.is_read is False
        assert notification.read_at is None
        assert notification.data == {}

    def test_data_can_store_json(self):
        notification = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
            data={
                "order_id": "123",
                "order_number": "QTA-20261001-000001",
            },
        )

        notification.refresh_from_db()

        assert notification.data["order_id"] == "123"
        assert notification.data["order_number"] == "QTA-20261001-000001"

    def test_notification_type_choices(self):
        notification = Notification(
            recipient=self.user,
            type="INVALID_TYPE",
            title="Test",
            message="Test message",
        )

        with pytest.raises(ValidationError):
            notification.full_clean()

    def test_rating_is_read_can_be_updated(self):
        notification = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
        )

        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])

        notification.refresh_from_db()

        assert notification.is_read is True

    def test_str(self):
        notification = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
        )

        assert str(notification) == "+201000000000 - New Order"

    def test_ordering_by_created_at_descending(self):
        from django.utils import timezone
        from datetime import timedelta

        first = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="First",
            message="First notification",
        )

        second = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_ACCEPTED,
            title="Second",
            message="Second notification",
        )

        first.created_at = timezone.now() - timedelta(minutes=1)
        first.save(update_fields=["created_at"])

        second.created_at = timezone.now()
        second.save(update_fields=["created_at"])

        notifications = list(Notification.objects.all())

        assert notifications[0].id == second.id
        assert notifications[1].id == first.id