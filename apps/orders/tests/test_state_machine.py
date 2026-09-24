import pytest

from apps.orders.constants import OrderStatus
from apps.orders.services.state_machine import validate_transition


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        (OrderStatus.CREATED, OrderStatus.ACCEPTED),
        (OrderStatus.CREATED, OrderStatus.REJECTED),
        (OrderStatus.CREATED, OrderStatus.CANCELLED),
        (OrderStatus.ACCEPTED, OrderStatus.PREPARING),
        (OrderStatus.ACCEPTED, OrderStatus.CANCELLED),
        (OrderStatus.PREPARING, OrderStatus.READY),
        (OrderStatus.PREPARING, OrderStatus.CANCELLED),
        (OrderStatus.READY, OrderStatus.OUT_FOR_DELIVERY),
        (OrderStatus.READY, OrderStatus.CANCELLED),
        (OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED),
        (OrderStatus.OUT_FOR_DELIVERY, OrderStatus.FAILED_DELIVERY),
        (OrderStatus.FAILED_DELIVERY, OrderStatus.OUT_FOR_DELIVERY),
        (OrderStatus.DELIVERED, OrderStatus.RETURNED),
        (OrderStatus.RETURNED, OrderStatus.REFUNDED),
    ],
)
def test_valid_order_transitions(current_status, new_status):
    validate_transition(
        current_status=current_status,
        new_status=new_status,
    )


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        (OrderStatus.CREATED, OrderStatus.DELIVERED),
        (OrderStatus.CREATED, OrderStatus.PREPARING),
        (OrderStatus.ACCEPTED, OrderStatus.DELIVERED),
        (OrderStatus.PREPARING, OrderStatus.DELIVERED),
        (OrderStatus.DELIVERED, OrderStatus.CANCELLED),
        (OrderStatus.DELIVERED, OrderStatus.ACCEPTED),
        (OrderStatus.REJECTED, OrderStatus.ACCEPTED),
        (OrderStatus.CANCELLED, OrderStatus.ACCEPTED),
        (OrderStatus.REFUNDED, OrderStatus.CREATED),
    ],
)
def test_invalid_order_transitions(current_status, new_status):
    with pytest.raises(ValueError, match="Invalid order transition"):
        validate_transition(
            current_status=current_status,
            new_status=new_status,
        )