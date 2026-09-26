from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.utils import timezone

from apps.orders.constants import (
    DeliveryAssignmentStatus,
    OrderStatus,
)
from apps.orders.models import (
    DeliveryAssignment,
    DeliveryOTP,
    Order,
)
from apps.orders.permissions import validate_actor_permission
from apps.orders.services.order import OrderService


class DeliveryAssignmentService:

    @staticmethod
    @transaction.atomic
    def assign(*, order_id, delivery_user, actor):
        order = (
            Order.objects
            .select_for_update()
            .get(id=order_id)
        )

        if delivery_user.role != "DELIVERY":
            raise ValueError(
                "Assigned user must have DELIVERY role."
            )

        active_assignment = (
            DeliveryAssignment.objects
            .select_for_update()
            .filter(
                order=order,
                status__in=[
                    DeliveryAssignmentStatus.ASSIGNED,
                    DeliveryAssignmentStatus.ACCEPTED,
                ],
            )
            .first()
        )

        if active_assignment:
            raise ValueError(
                "Order already has an active delivery assignment."
            )

        if order.status != OrderStatus.READY:
            raise ValueError(
                "Only READY orders can be assigned for delivery."
            )

        validate_actor_permission(
            actor=actor,
            current_status=order.status,
            new_status=OrderStatus.OUT_FOR_DELIVERY,
        )

        assignment = DeliveryAssignment.objects.create(
            order=order,
            delivery_user=delivery_user,
            status=DeliveryAssignmentStatus.ASSIGNED,
        )

        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.OUT_FOR_DELIVERY,
            actor=actor,
        )

        return assignment

    @staticmethod
    @transaction.atomic
    def accept(*, assignment_id, actor):
        assignment = (
            DeliveryAssignment.objects
            .select_for_update()
            .select_related("order", "delivery_user")
            .get(id=assignment_id)
        )

        if actor.role != "DELIVERY":
            raise PermissionError(
                "Only DELIVERY users can accept assignments."
            )

        if assignment.delivery_user_id != actor.id:
            raise PermissionError(
                "Only the assigned delivery user can accept this assignment."
            )

        if assignment.status != DeliveryAssignmentStatus.ASSIGNED:
            raise ValueError(
                "Only ASSIGNED deliveries can be accepted."
            )

        assignment.status = DeliveryAssignmentStatus.ACCEPTED
        assignment.accepted_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "accepted_at",
                "updated_at",
            ]
        )

        return assignment

    @staticmethod
    @transaction.atomic
    def cancel(*, assignment_id, actor):
        assignment = (
            DeliveryAssignment.objects
            .select_for_update()
            .select_related("order", "delivery_user")
            .get(id=assignment_id)
        )

        is_admin = actor.role in {
            "ADMIN",
            "SUPER_ADMIN",
        }

        is_assigned_delivery = (
            actor.role == "DELIVERY"
            and assignment.delivery_user_id == actor.id
        )

        if not (is_admin or is_assigned_delivery):
            raise PermissionError(
                "You do not have permission to cancel this assignment."
            )

        if assignment.status not in {
            DeliveryAssignmentStatus.ASSIGNED,
            DeliveryAssignmentStatus.ACCEPTED,
        }:
            raise ValueError(
                "Only active delivery assignments can be cancelled."
            )

        assignment.status = DeliveryAssignmentStatus.CANCELLED

        assignment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return assignment

    @staticmethod
    def complete_delivery(
        *,
        assignment_id,
        otp_id,
        code,
        actor,
    ):
        # ==========================================================
        # STEP 1
        # Validate OTP BEFORE starting the delivery transaction.
        #
        # Failed attempts are therefore committed independently.
        # ==========================================================

        otp_error = None

        with transaction.atomic():
            assignment = (
                DeliveryAssignment.objects
                .select_related("order")
                .filter(id=assignment_id)
                .first()
            )

            if assignment is None:
                raise DeliveryAssignment.DoesNotExist

            if actor.role != "DELIVERY":
                raise PermissionError(
                    "Only DELIVERY users can complete deliveries."
                )

            if assignment.delivery_user_id != actor.id:
                raise PermissionError(
                    "Only the assigned delivery user can complete this delivery."
                )

            if assignment.status != DeliveryAssignmentStatus.ACCEPTED:
                raise ValueError(
                    "Only ACCEPTED delivery assignments can be completed."
                )

            if assignment.order.status != OrderStatus.OUT_FOR_DELIVERY:
                raise ValueError(
                    "Only OUT_FOR_DELIVERY orders can be completed."
                )

            otp = (
                DeliveryOTP.objects
                .select_for_update()
                .filter(
                    id=otp_id,
                    order_id=assignment.order_id,
                )
                .first()
            )

            if otp is None:
                otp_error = "Delivery OTP not found."

            elif otp.status != "ACTIVE":
                otp_error = "Delivery OTP is not active."

            else:
                now = timezone.now()

                if now >= otp.expires_at:
                    otp.status = "EXPIRED"

                    otp.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

                    otp_error = "Delivery OTP has expired."

                elif otp.attempts >= otp.max_attempts:
                    otp.status = "BLOCKED"

                    otp.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

                    otp_error = "Delivery OTP is blocked."

                elif not check_password(code, otp.code_hash):
                    otp.attempts += 1

                    if otp.attempts >= otp.max_attempts:
                        otp.status = "BLOCKED"

                    otp.save(
                        update_fields=[
                            "attempts",
                            "status",
                            "updated_at",
                        ]
                    )

                    otp_error = "Invalid delivery OTP."

                else:
                    # OTP is valid.
                    # Do NOT mark it VERIFIED here.
                    #
                    # We only return its ID and perform the actual
                    # verification inside the delivery transaction.
                    otp_error = None

            otp_id = otp.id if otp else otp_id

        # Important:
        # The atomic block above has already committed any failed
        # attempt before we continue.
        if otp_error:
            raise ValueError(otp_error)

        # ==========================================================
        # STEP 2
        # Successful delivery transaction.
        #
        # OTP verification + inventory sale + order transition +
        # assignment completion are ONE atomic operation.
        # ==========================================================

        with transaction.atomic():

            assignment = (
                DeliveryAssignment.objects
                .select_for_update()
                .select_related(
                    "order",
                    "delivery_user",
                )
                .get(id=assignment_id)
            )

            if actor.role != "DELIVERY":
                raise PermissionError(
                    "Only DELIVERY users can complete deliveries."
                )

            if assignment.delivery_user_id != actor.id:
                raise PermissionError(
                    "Only the assigned delivery user can complete this delivery."
                )

            if assignment.status != DeliveryAssignmentStatus.ACCEPTED:
                raise ValueError(
                    "Only ACCEPTED delivery assignments can be completed."
                )

            order = (
                Order.objects
                .select_for_update()
                .get(id=assignment.order_id)
            )

            if order.status != OrderStatus.OUT_FOR_DELIVERY:
                raise ValueError(
                    "Only OUT_FOR_DELIVERY orders can be completed."
                )

            # Re-lock the OTP inside the actual delivery transaction.
            otp = (
                DeliveryOTP.objects
                .select_for_update()
                .get(
                    id=otp_id,
                    order_id=order.id,
                )
            )

            # Another request may have used the OTP between STEP 1
            # and STEP 2.
            if otp.status != "ACTIVE":
                raise ValueError(
                    "Delivery OTP is no longer active."
                )

            # Re-check the code while holding the row lock.
            if not check_password(code, otp.code_hash):
                raise ValueError(
                    "Invalid delivery OTP."
                )

            # Now the OTP becomes part of the atomic delivery transaction.
            otp.status = "VERIFIED"
            otp.verified_at = timezone.now()

            otp.save(
                update_fields=[
                    "status",
                    "verified_at",
                    "updated_at",
                ]
            )

            # Complete order + sell reserved inventory.
            OrderService.transition_status(
                order_id=order.id,
                new_status=OrderStatus.DELIVERED,
                actor=actor,
                delivery_otp_id=otp.id,
            )

            assignment.status = DeliveryAssignmentStatus.DELIVERED
            assignment.completed_at = timezone.now()

            assignment.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "updated_at",
                ]
            )

            return assignment