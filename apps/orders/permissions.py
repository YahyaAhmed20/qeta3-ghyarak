from apps.orders.constants import OrderStatus


ALLOWED_ROLE_TRANSITIONS = {
    "SELLER_OWNER": {
        OrderStatus.CREATED: {
            OrderStatus.ACCEPTED,
            OrderStatus.REJECTED,
        },
        OrderStatus.ACCEPTED: {
            OrderStatus.PREPARING,
        },
        OrderStatus.PREPARING: {
            OrderStatus.READY,
        },
    },

    "SELLER_MANAGER": {
        OrderStatus.CREATED: {
            OrderStatus.ACCEPTED,
            OrderStatus.REJECTED,
        },
        OrderStatus.ACCEPTED: {
            OrderStatus.PREPARING,
        },
        OrderStatus.PREPARING: {
            OrderStatus.READY,
        },
    },

    "SELLER_STAFF": {
        OrderStatus.ACCEPTED: {
            OrderStatus.PREPARING,
        },
        OrderStatus.PREPARING: {
            OrderStatus.READY,
        },
    },

    "DELIVERY": {
        OrderStatus.READY: {
            OrderStatus.OUT_FOR_DELIVERY,
        },
        OrderStatus.OUT_FOR_DELIVERY: {
            OrderStatus.DELIVERED,
            OrderStatus.FAILED_DELIVERY,
        },
        OrderStatus.FAILED_DELIVERY: {
            OrderStatus.OUT_FOR_DELIVERY,
        },
    },

    "CUSTOMER": {
        OrderStatus.CREATED: {
            OrderStatus.CANCELLED,
        },
        OrderStatus.ACCEPTED: {
            OrderStatus.CANCELLED,
        },
        OrderStatus.PREPARING: {
            OrderStatus.CANCELLED,
        },
        OrderStatus.READY: {
            OrderStatus.CANCELLED,
        },
    },

    "ADMIN": {
        OrderStatus.CREATED: {
            OrderStatus.ACCEPTED,
            OrderStatus.REJECTED,
            OrderStatus.CANCELLED,
        },
        OrderStatus.ACCEPTED: {
            OrderStatus.PREPARING,
            OrderStatus.CANCELLED,
        },
        OrderStatus.PREPARING: {
            OrderStatus.READY,
            OrderStatus.CANCELLED,
        },
        OrderStatus.READY: {
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.CANCELLED,
        },
        OrderStatus.OUT_FOR_DELIVERY: {
            OrderStatus.DELIVERED,
            OrderStatus.FAILED_DELIVERY,
        },
        OrderStatus.FAILED_DELIVERY: {
            OrderStatus.OUT_FOR_DELIVERY,
        },
        OrderStatus.DELIVERED: {
            OrderStatus.RETURNED,
        },
        OrderStatus.RETURNED: {
            OrderStatus.REFUNDED,
        },
    },

    "SUPER_ADMIN": {
        OrderStatus.CREATED: {
            OrderStatus.ACCEPTED,
            OrderStatus.REJECTED,
            OrderStatus.CANCELLED,
        },
        OrderStatus.ACCEPTED: {
            OrderStatus.PREPARING,
            OrderStatus.CANCELLED,
        },
        OrderStatus.PREPARING: {
            OrderStatus.READY,
            OrderStatus.CANCELLED,
        },
        OrderStatus.READY: {
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.CANCELLED,
        },
        OrderStatus.OUT_FOR_DELIVERY: {
            OrderStatus.DELIVERED,
            OrderStatus.FAILED_DELIVERY,
        },
        OrderStatus.FAILED_DELIVERY: {
            OrderStatus.OUT_FOR_DELIVERY,
        },
        OrderStatus.DELIVERED: {
            OrderStatus.RETURNED,
        },
        OrderStatus.RETURNED: {
            OrderStatus.REFUNDED,
        },
    },
}


def validate_actor_permission(*, actor, current_status, new_status):
    role_transitions = ALLOWED_ROLE_TRANSITIONS.get(actor.role, {})

    allowed_statuses = role_transitions.get(current_status, set())

    if new_status not in allowed_statuses:
        raise PermissionError(
            f"Role {actor.role} cannot transition "
            f"{current_status} -> {new_status}"
        )