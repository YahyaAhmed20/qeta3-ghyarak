import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification
from apps.notifications.services.notification import NotificationService


User = get_user_model()


@pytest.mark.django_db
class TestNotificationService:

    def setup_method(self):
        self.user = User.objects.create_user(
            phone="01000000000",
            password="TestPassword123",
        )

    def test_create_notification(self):
        notification = NotificationService.create(
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
        assert notification.is_read is False

    def test_create_notification_with_data(self):
        notification = NotificationService.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
            data={
                "order_id": "123",
                "order_number": "QTA-20261001-000001",
            },
        )

        assert notification.data == {
            "order_id": "123",
            "order_number": "QTA-20261001-000001",
        }

    def test_create_notification_without_data(self):
        notification = NotificationService.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
        )

        assert notification.data == {}

    def test_mark_as_read(self):
        notification = NotificationService.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
        )

        updated_notification = NotificationService.mark_as_read(
            notification=notification,
        )

        updated_notification.refresh_from_db()

        assert updated_notification.is_read is True
        assert updated_notification.read_at is not None

    def test_mark_as_read_is_idempotent(self):
        notification = NotificationService.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="New Order",
            message="You have a new order.",
        )

        first_result = NotificationService.mark_as_read(
            notification=notification,
        )

        first_result.refresh_from_db()
        first_read_at = first_result.read_at

        second_result = NotificationService.mark_as_read(
            notification=first_result,
        )

        second_result.refresh_from_db()

        assert second_result.is_read is True
        assert second_result.read_at == first_read_at