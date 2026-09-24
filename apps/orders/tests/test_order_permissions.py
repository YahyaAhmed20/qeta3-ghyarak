import pytest

from apps.orders.constants import OrderStatus
from apps.orders.permissions import validate_actor_permission


@pytest.mark.parametrize(
    "role,current_status,new_status",
    [
        ("SELLER_OWNER", OrderStatus.CREATED, OrderStatus.ACCEPTED),
        ("SELLER_OWNER", OrderStatus.CREATED, OrderStatus.REJECTED),
        ("SELLER_OWNER", OrderStatus.ACCEPTED, OrderStatus.PREPARING),
        ("SELLER_OWNER", OrderStatus.PREPARING, OrderStatus.READY),

        ("SELLER_MANAGER", OrderStatus.CREATED, OrderStatus.ACCEPTED),
        ("SELLER_MANAGER", OrderStatus.ACCEPTED, OrderStatus.PREPARING),

        ("SELLER_STAFF", OrderStatus.ACCEPTED, OrderStatus.PREPARING),
        ("SELLER_STAFF", OrderStatus.PREPARING, OrderStatus.READY),

        ("DELIVERY", OrderStatus.READY, OrderStatus.OUT_FOR_DELIVERY),
        ("DELIVERY", OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED),
        ("DELIVERY", OrderStatus.OUT_FOR_DELIVERY, OrderStatus.FAILED_DELIVERY),
        ("DELIVERY", OrderStatus.FAILED_DELIVERY, OrderStatus.OUT_FOR_DELIVERY),

        ("CUSTOMER", OrderStatus.CREATED, OrderStatus.CANCELLED),
        ("CUSTOMER", OrderStatus.ACCEPTED, OrderStatus.CANCELLED),
        ("CUSTOMER", OrderStatus.PREPARING, OrderStatus.CANCELLED),
        ("CUSTOMER", OrderStatus.READY, OrderStatus.CANCELLED),

        ("ADMIN", OrderStatus.DELIVERED, OrderStatus.RETURNED),
        ("ADMIN", OrderStatus.RETURNED, OrderStatus.REFUNDED),

        ("SUPER_ADMIN", OrderStatus.DELIVERED, OrderStatus.RETURNED),
        ("SUPER_ADMIN", OrderStatus.RETURNED, OrderStatus.REFUNDED),
    ],
)
def test_allowed_role_transitions(
    role,
    current_status,
    new_status,
):
    class Actor:
        pass

    actor = Actor()
    actor.role = role

    validate_actor_permission(
        actor=actor,
        current_status=current_status,
        new_status=new_status,
    )


@pytest.mark.parametrize(
    "role,current_status,new_status",
    [
        ("CUSTOMER", OrderStatus.CREATED, OrderStatus.ACCEPTED),
        ("CUSTOMER", OrderStatus.DELIVERED, OrderStatus.CANCELLED),

        ("DELIVERY", OrderStatus.CREATED, OrderStatus.ACCEPTED),
        ("DELIVERY", OrderStatus.ACCEPTED, OrderStatus.PREPARING),

        ("SELLER_OWNER", OrderStatus.READY, OrderStatus.OUT_FOR_DELIVERY),
        ("SELLER_STAFF", OrderStatus.CREATED, OrderStatus.ACCEPTED),

        ("ADMIN", OrderStatus.REFUNDED, OrderStatus.ACCEPTED),

        ("UNKNOWN", OrderStatus.CREATED, OrderStatus.ACCEPTED),
    ],
)
def test_forbidden_role_transitions(
    role,
    current_status,
    new_status,
):
    class Actor:
        pass

    actor = Actor()
    actor.role = role

    with pytest.raises(
        PermissionError,
        match="cannot transition",
    ):
        validate_actor_permission(
            actor=actor,
            current_status=current_status,
            new_status=new_status,
        )