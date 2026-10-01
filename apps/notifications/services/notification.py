from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification


class NotificationService:

    @staticmethod
    @transaction.atomic
    def create(
        *,
        recipient,
        type,
        title,
        message,
        data=None,
    ):
        notification = Notification(
            recipient=recipient,
            type=type,
            title=title,
            message=message,
            data=data or {},
        )

        notification.full_clean()
        notification.save()

        return notification

    @staticmethod
    @transaction.atomic
    def mark_as_read(*, notification):
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(
                update_fields=[
                    "is_read",
                    "read_at",
                    "updated_at",
                ]
            )

        return notification

    @staticmethod
    @transaction.atomic
    def mark_all_as_read(*, user):
        now = timezone.now()

        updated_count = (
            Notification.objects
            .filter(
                recipient=user,
                is_read=False,
            )
            .update(
                is_read=True,
                read_at=now,
                updated_at=now,
            )
        )

        return updated_count