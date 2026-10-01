from django.urls import path

from apps.notifications.api.views import (
    NotificationListAPIView,
    NotificationMarkAsReadAPIView,
    NotificationDetailAPIView,
    NotificationUnreadCountAPIView,
    NotificationMarkAllAsReadAPIView,
)


urlpatterns = [
    path(
        "",
        NotificationListAPIView.as_view(),
        name="notification-list",
    ),
    path(
        "unread-count/",
        NotificationUnreadCountAPIView.as_view(),
        name="notification-unread-count",
    ),
    path(
        "read-all/",
        NotificationMarkAllAsReadAPIView.as_view(),
        name="notification-mark-all-as-read",
),
    path(
        "<uuid:notification_id>/read/",
        NotificationMarkAsReadAPIView.as_view(),
        name="notification-mark-as-read",
    ),
    path(
        "<uuid:notification_id>/",
        NotificationDetailAPIView.as_view(),
        name="notification-detail",
    ),
]