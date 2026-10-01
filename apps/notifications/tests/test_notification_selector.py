import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import Notification
from apps.notifications.selectors.notification import NotificationSelector


User = get_user_model()


@pytest.mark.django_db
class TestNotificationSelector:

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
        notification_type=Notification.NotificationType.ORDER_CREATED,
    ):
        return Notification.objects.create(
            recipient=recipient,
            type=notification_type,
            title=title,
            message=f"{title} message",
            is_read=is_read,
        )

    def test_get_notification(self):
        notification = self.create_notification(
            recipient=self.user,
            title="Order Created",
        )

        result = NotificationSelector.get_notification(
            notification_id=notification.id,
        )

        assert result is not None
        assert result.id == notification.id
        assert result.recipient == self.user

    def test_get_notification_returns_none_for_invalid_id(self):
        result = NotificationSelector.get_notification(
            notification_id="00000000-0000-0000-0000-000000000000",
        )

        assert result is None

    def test_get_user_notifications(self):
        first = self.create_notification(
            recipient=self.user,
            title="First",
        )

        second = self.create_notification(
            recipient=self.user,
            title="Second",
        )

        self.create_notification(
            recipient=self.other_user,
            title="Other User",
        )

        notifications = list(
            NotificationSelector.get_user_notifications(
                user_id=self.user.id,
            )
        )

        assert len(notifications) == 2
        assert {notification.id for notification in notifications} == {
            first.id,
            second.id,
        }

    def test_get_unread_notifications(self):
        unread = self.create_notification(
            recipient=self.user,
            title="Unread",
            is_read=False,
        )

        self.create_notification(
            recipient=self.user,
            title="Read",
            is_read=True,
        )

        self.create_notification(
            recipient=self.other_user,
            title="Other User",
            is_read=False,
        )

        notifications = list(
            NotificationSelector.get_unread_notifications(
                user_id=self.user.id,
            )
        )

        assert len(notifications) == 1
        assert notifications[0].id == unread.id

    def test_get_user_notifications_returns_empty_for_user_without_notifications(self):
        notifications = list(
            NotificationSelector.get_user_notifications(
                user_id=self.user.id,
            )
        )

        assert notifications == []

    def test_get_unread_notifications_returns_empty_when_all_are_read(self):
        self.create_notification(
            recipient=self.user,
            title="Read 1",
            is_read=True,
        )

        self.create_notification(
            recipient=self.user,
            title="Read 2",
            is_read=True,
        )

        notifications = list(
            NotificationSelector.get_unread_notifications(
                user_id=self.user.id,
            )
        )

        assert notifications == []