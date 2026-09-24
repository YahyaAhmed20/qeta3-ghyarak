from apps.orders.constants import OrderStatus


ALLOWED_TRANSITIONS = {
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
    OrderStatus.REJECTED: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.REFUNDED: set(),
}


def validate_transition(*, current_status, new_status):
    allowed_statuses = ALLOWED_TRANSITIONS.get(current_status, set())

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Invalid order transition: "
            f"{current_status} -> {new_status}"
        )