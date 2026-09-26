from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.constants import DeliveryAssignmentStatus
from apps.orders.models import DeliveryAssignment
from apps.orders.services.delivery_assignment import (
    DeliveryAssignmentService,
)

from apps.orders.api.serializers import (
    DeliveryAssignmentCreateSerializer,
)


class DeliveryAssignmentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        if request.user.role not in {
            "ADMIN",
            "SUPER_ADMIN",
        }:
            return Response(
                {
                    "detail": (
                        "Only ADMIN or SUPER_ADMIN "
                        "can assign delivery orders."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DeliveryAssignmentCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        delivery_user = serializer.validated_data[
            "delivery_user_id"
        ]

        try:
            assignment = DeliveryAssignmentService.assign(
                order_id=order_id,
                delivery_user=delivery_user,
                actor=request.user,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "id": str(assignment.id),
                "order_id": str(assignment.order_id),
                "delivery_user_id": str(
                    assignment.delivery_user_id
                ),
                "status": assignment.status,
                "assigned_at": assignment.assigned_at,
            },
            status=status.HTTP_201_CREATED,
        )


class DeliveryAssignmentAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        try:
            assignment = DeliveryAssignmentService.accept(
                assignment_id=assignment_id,
                actor=request.user,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except DeliveryAssignment.DoesNotExist:
            return Response(
                {"detail": "Delivery assignment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "id": str(assignment.id),
                "order_id": str(assignment.order_id),
                "delivery_user_id": str(assignment.delivery_user_id),
                "status": assignment.status,
                "accepted_at": assignment.accepted_at,
            },
            status=status.HTTP_200_OK,
        )


class DeliveryAssignmentCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        try:
            assignment = DeliveryAssignmentService.cancel(
                assignment_id=assignment_id,
                actor=request.user,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except DeliveryAssignment.DoesNotExist:
            return Response(
                {"detail": "Delivery assignment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "id": str(assignment.id),
                "order_id": str(assignment.order_id),
                "delivery_user_id": str(assignment.delivery_user_id),
                "status": assignment.status,
            },
            status=status.HTTP_200_OK,
        )


class DeliveryAssignmentCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assignment_id):
        otp_id = request.data.get("otp_id")
        code = request.data.get("code")

        if not otp_id or not code:
            return Response(
                {
                    "detail": "otp_id and code are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            assignment = DeliveryAssignmentService.complete_delivery(
                assignment_id=assignment_id,
                otp_id=otp_id,
                code=code,
                actor=request.user,
            )

        except DeliveryAssignment.DoesNotExist:
            return Response(
                {"detail": "Delivery assignment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "id": str(assignment.id),
                "order_id": str(assignment.order_id),
                "status": assignment.status,
                "completed_at": assignment.completed_at,
            },
            status=status.HTTP_200_OK,
        )