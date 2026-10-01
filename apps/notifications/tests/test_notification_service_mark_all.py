import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification
from apps.notifications.services.notification import NotificationService


User = get_user_model()


@pytest.mark.django_db
class TestNotificationServiceMarkAll:

    def setup_method(self):
        self.user = User.objects.create_user(
            phone="01000000000",
            password="TestPassword123",
        )

        self.other_user = User.objects.create_user(
            phone="01111111111",
            password="TestPassword123",
        )

    def create_notification(
        self,
        *,
        recipient,
        title="Notification",
        is_read=False,
    ):
        return Notification.objects.create(
            recipient=recipient,
            type=Notification.NotificationType.ORDER_CREATED,
            title=title,
            message=f"{title} message",
            is_read=is_read,
        )

    def test_mark_all_as_read(self):
        first = self.create_notification(
            recipient=self.user,
            title="First",
        )

        second = self.create_notification(
            recipient=self.user,
            title="Second",
        )

        self.create_notification(
            recipient=self.user,
            title="Already Read",
            is_read=True,
        )

        NotificationService.mark_all_as_read(
            user=self.user,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        assert first.is_read is True
        assert first.read_at is not None

        assert second.is_read is True
        assert second.read_at is not None

    def test_mark_all_as_read_does_not_affect_other_users(self):
        notification = self.create_notification(
            recipient=self.other_user,
            title="Other User",
        )

        NotificationService.mark_all_as_read(
            user=self.user,
        )

        notification.refresh_from_db()

        assert notification.is_read is False
        assert notification.read_at is None

    def test_mark_all_as_read_when_no_unread_notifications(self):
        notification = self.create_notification(
            recipient=self.user,
            title="Already Read",
            is_read=True,
        )

        original_read_at = notification.read_at

        NotificationService.mark_all_as_read(
            user=self.user,
        )

        notification.refresh_from_db()

        assert notification.is_read is True
        assert notification.read_at == original_read_at

    def test_mark_all_as_read_returns_updated_count(self):
        self.create_notification(
            recipient=self.user,
            title="First",
        )

        self.create_notification(
            recipient=self.user,
            title="Second",
        )

        self.create_notification(
            recipient=self.user,
            title="Read",
            is_read=True,
        )

        result = NotificationService.mark_all_as_read(
            user=self.user,
        )

        assert result == 2