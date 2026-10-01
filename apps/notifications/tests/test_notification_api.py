import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.notifications.models import Notification


User = get_user_model()


@pytest.mark.django_db
class TestNotificationListAPI:

    def setup_method(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            phone="01000000000",
            password="TestPassword123",
        )

        self.other_user = User.objects.create_user(
            phone="01111111111",
            password="TestPassword123",
        )

        self.url = "/api/notifications/"

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

    def test_unauthenticated_user_cannot_list_notifications(self):
        response = self.client.get(self.url)

        assert response.status_code == 401

    def test_user_can_list_own_notifications(self):
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

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.data["count"] == 2

        returned_ids = {
            item["id"]
            for item in response.data["results"]
        }

        assert returned_ids == {
            str(first.id),
            str(second.id),
        }

    def test_user_cannot_see_other_users_notifications(self):
        self.create_notification(
            recipient=self.other_user,
            title="Private Notification",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_notifications_are_returned_newest_first(self):
        first = self.create_notification(
            recipient=self.user,
            title="First",
        )

        second = self.create_notification(
            recipient=self.user,
            title="Second",
        )

        from django.utils import timezone
        from datetime import timedelta

        first.created_at = timezone.now() - timedelta(minutes=1)
        first.save(update_fields=["created_at"])

        second.created_at = timezone.now()
        second.save(update_fields=["created_at"])

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.data["results"][0]["id"] == str(second.id)
        assert response.data["results"][1]["id"] == str(first.id)

    def test_unauthenticated_user_cannot_mark_notification_as_read(self):
        notification = self.create_notification(
            recipient=self.user,
        )

        url = f"/api/notifications/{notification.id}/read/"

        response = self.client.patch(url)

        assert response.status_code == 401

    def test_user_can_mark_own_notification_as_read(self):
        notification = self.create_notification(
            recipient=self.user,
        )

        self.client.force_authenticate(user=self.user)

        url = f"/api/notifications/{notification.id}/read/"

        response = self.client.patch(url)

        assert response.status_code == 200
        assert response.data["id"] == str(notification.id)
        assert response.data["is_read"] is True
        assert response.data["read_at"] is not None

        notification.refresh_from_db()

        assert notification.is_read is True
        assert notification.read_at is not None

    def test_user_cannot_mark_other_users_notification_as_read(self):
        notification = self.create_notification(
            recipient=self.other_user,
        )

        self.client.force_authenticate(user=self.user)

        url = f"/api/notifications/{notification.id}/read/"

        response = self.client.patch(url)

        assert response.status_code == 404

        notification.refresh_from_db()

        assert notification.is_read is False
        assert notification.read_at is None

    def test_mark_as_read_is_idempotent(self):
        notification = self.create_notification(
            recipient=self.user,
        )

        self.client.force_authenticate(user=self.user)

        url = f"/api/notifications/{notification.id}/read/"

        first_response = self.client.patch(url)

        assert first_response.status_code == 200

        notification.refresh_from_db()
        first_read_at = notification.read_at

        second_response = self.client.patch(url)

        assert second_response.status_code == 200

        notification.refresh_from_db()

        assert notification.is_read is True
        assert notification.read_at == first_read_at

    def test_mark_as_read_returns_404_for_nonexistent_notification(self):
        self.client.force_authenticate(user=self.user)

        url = (
            "/api/notifications/"
            "00000000-0000-0000-0000-000000000000/"
            "read/"
        )

        response = self.client.patch(url)

        assert response.status_code == 404

    def test_user_can_get_own_notification(self):
        notification = self.create_notification(
            recipient=self.user,
            title="My Notification",
        )

        self.client.force_authenticate(user=self.user)

        url = f"/api/notifications/{notification.id}/"

        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == str(notification.id)
        assert response.data["title"] == "My Notification"
        assert response.data["message"] == "My Notification message"

    def test_user_cannot_get_other_users_notification(self):
        notification = self.create_notification(
            recipient=self.other_user,
            title="Private Notification",
        )

        self.client.force_authenticate(user=self.user)

        url = f"/api/notifications/{notification.id}/"

        response = self.client.get(url)

        assert response.status_code == 404

    def test_unauthenticated_user_cannot_get_notification(self):
        notification = self.create_notification(
            recipient=self.user,
        )

        url = f"/api/notifications/{notification.id}/"

        response = self.client.get(url)

        assert response.status_code == 401

    def test_get_nonexistent_notification_returns_404(self):
        self.client.force_authenticate(user=self.user)

        url = (
            "/api/notifications/"
            "00000000-0000-0000-0000-000000000000/"
        )

        response = self.client.get(url)

        assert response.status_code == 404

    def test_user_can_get_unread_notifications_count(self):
        self.create_notification(
            recipient=self.user,
            title="Unread 1",
            is_read=False,
        )

        self.create_notification(
            recipient=self.user,
            title="Unread 2",
            is_read=False,
        )

        self.create_notification(
            recipient=self.user,
            title="Read",
            is_read=True,
        )

        self.create_notification(
            recipient=self.other_user,
            title="Other User Unread",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        url = "/api/notifications/unread-count/"

        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_unread_count_is_zero_when_user_has_no_unread_notifications(self):
        self.create_notification(
            recipient=self.user,
            title="Read",
            is_read=True,
        )

        self.client.force_authenticate(user=self.user)

        url = "/api/notifications/unread-count/"

        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_unread_count_does_not_include_other_users_notifications(self):
        self.create_notification(
            recipient=self.other_user,
            title="Other User Unread",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        url = "/api/notifications/unread-count/"

        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_unauthenticated_user_cannot_get_unread_count(self):
        url = "/api/notifications/unread-count/"

        response = self.client.get(url)

        assert response.status_code == 401

    def test_mark_all_as_read(self):
        self.client.force_authenticate(user=self.user)

        first = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="First",
            message="First message",
        )

        second = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_ACCEPTED,
            title="Second",
            message="Second message",
        )

        response = self.client.patch(
            "/api/notifications/read-all/",
        )

        assert response.status_code == 200
        assert response.data["updated_count"] == 2

        first.refresh_from_db()
        second.refresh_from_db()

        assert first.is_read is True
        assert first.read_at is not None

        assert second.is_read is True
        assert second.read_at is not None

    def test_mark_all_as_read_does_not_affect_other_users(self):
        self.client.force_authenticate(user=self.user)

        notification = Notification.objects.create(
            recipient=self.other_user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="Other User",
            message="Other user message",
        )

        response = self.client.patch(
            "/api/notifications/read-all/",
        )

        assert response.status_code == 200
        assert response.data["updated_count"] == 0

        notification.refresh_from_db()

        assert notification.is_read is False
        assert notification.read_at is None

    def test_mark_all_as_read_keeps_already_read_notifications_unchanged(self):
        self.client.force_authenticate(user=self.user)

        notification = Notification.objects.create(
            recipient=self.user,
            type=Notification.NotificationType.ORDER_CREATED,
            title="Already Read",
            message="Already read message",
            is_read=True,
        )

        original_read_at = notification.read_at

        response = self.client.patch(
            "/api/notifications/read-all/",
        )

        assert response.status_code == 200
        assert response.data["updated_count"] == 0

        notification.refresh_from_db()

        assert notification.is_read is True
        assert notification.read_at == original_read_at

    def test_mark_all_as_read_with_no_notifications(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            "/api/notifications/read-all/",
        )

        assert response.status_code == 200
        assert response.data["updated_count"] == 0

    def test_mark_all_as_read_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.patch(
            "/api/notifications/read-all/",
        )

        assert response.status_code == 401