from uuid import UUID
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.api.serializers import NotificationSerializer
from apps.notifications.models import Notification
from apps.notifications.selectors.notification import NotificationSelector
from apps.notifications.services.notification import NotificationService


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = NotificationSelector.get_user_notifications(
            user_id=request.user.id,
        )

        serializer = NotificationSerializer(
            notifications,
            many=True,
        )

        return Response(
            {
                "count": len(serializer.data),
                "results": serializer.data,
            },
            status=200,
        )


class NotificationMarkAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        try:
            notification_id = UUID(str(notification_id))
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid notification ID."},
                status=400,
            )

        notification = get_object_or_404(
            Notification.objects.filter(
                id=notification_id,
                recipient=request.user,
            )
        )

        notification = NotificationService.mark_as_read(
            notification=notification,
        )

        return Response(
            NotificationSerializer(notification).data,
            status=200,
        )
        
class NotificationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, notification_id):
        notification = get_object_or_404(
            Notification.objects.select_related("recipient"),
            id=notification_id,
            recipient=request.user,
        )

        return Response(
            NotificationSerializer(notification).data,
            status=200,
        )
        
class NotificationUnreadCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        return Response(
            {"count": count},
            status=200,
        )
        
        
class NotificationMarkAllAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        updated_count = NotificationService.mark_all_as_read(
            user=request.user,
        )

        return Response(
            {
                "updated_count": updated_count,
            },
            status=200,
        )