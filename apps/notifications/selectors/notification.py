from apps.notifications.models import Notification


class NotificationSelector:

    @staticmethod
    def get_notification(*, notification_id):
        return (
            Notification.objects
            .select_related("recipient")
            .filter(id=notification_id)
            .first()
        )

    @staticmethod
    def get_user_notifications(*, user_id):
        return (
            Notification.objects
            .select_related("recipient")
            .filter(recipient_id=user_id)
        )

    @staticmethod
    def get_unread_notifications(*, user_id):
        return (
            Notification.objects
            .select_related("recipient")
            .filter(
                recipient_id=user_id,
                is_read=False,
            )
        )