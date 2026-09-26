import pytest
from rest_framework.test import APIClient

from apps.orders.constants import (
    DeliveryAssignmentStatus,
    OrderStatus,
)
from apps.orders.models import DeliveryAssignment
from apps.orders.services.order import OrderService


@pytest.mark.django_db
class TestDeliveryAssignmentAPI:

    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def admin_user(self, django_user_model):
        return django_user_model.objects.create_user(
            phone="+201001234572",
            role="ADMIN",
            is_active=True,
        )

    @pytest.fixture
    def seller_owner(self, django_user_model):
        return django_user_model.objects.create_user(
            phone="+201001234573",
            role="SELLER_OWNER",
            is_active=True,
        )

    @pytest.fixture
    def delivery_user(self, django_user_model):
        return django_user_model.objects.create_user(
            phone="+201001234574",
            role="DELIVERY",
            is_active=True,
        )

    @pytest.fixture
    def another_delivery_user(self, django_user_model):
        return django_user_model.objects.create_user(
            phone="+201001234575",
            role="DELIVERY",
            is_active=True,
        )

    @pytest.fixture
    def ready_order(self, order, seller_owner):
        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.ACCEPTED,
            actor=seller_owner,
        )

        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.PREPARING,
            actor=seller_owner,
        )

        OrderService.transition_status(
            order_id=order.id,
            new_status=OrderStatus.READY,
            actor=seller_owner,
        )

        order.refresh_from_db()
        return order

    def authenticate(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client

    def test_admin_can_assign_delivery(
        self,
        api_client,
        admin_user,
        delivery_user,
        ready_order,
    ):
        self.authenticate(api_client, admin_user)

        response = api_client.post(
            f"/api/v1/orders/{ready_order.id}/delivery/assign/",
            {
                "delivery_user_id": str(delivery_user.id),
            },
            format="json",
        )

        assert response.status_code == 201

        assignment = DeliveryAssignment.objects.get(
            order=ready_order,
        )

        assert assignment.delivery_user_id == delivery_user.id
        assert assignment.status == DeliveryAssignmentStatus.ASSIGNED

        assert response.data["order_id"] == str(ready_order.id)
        assert response.data["delivery_user_id"] == str(
            delivery_user.id
        )

    def test_non_admin_cannot_assign_delivery(
        self,
        api_client,
        seller_owner,
        delivery_user,
        ready_order,
    ):
        self.authenticate(api_client, seller_owner)

        response = api_client.post(
            f"/api/v1/orders/{ready_order.id}/delivery/assign/",
            {
                "delivery_user_id": str(delivery_user.id),
            },
            format="json",
        )

        assert response.status_code == 403

        assert not DeliveryAssignment.objects.filter(
            order=ready_order,
        ).exists()

    def test_invalid_delivery_user_returns_400(
        self,
        api_client,
        admin_user,
        ready_order,
    ):
        self.authenticate(api_client, admin_user)

        response = api_client.post(
            f"/api/v1/orders/{ready_order.id}/delivery/assign/",
            {
                "delivery_user_id": (
                    "00000000-0000-0000-0000-000000000000"
                ),
            },
            format="json",
        )

        assert response.status_code == 400

    def test_non_ready_order_cannot_be_assigned(
        self,
        api_client,
        admin_user,
        delivery_user,
        order,
    ):
        self.authenticate(api_client, admin_user)

        response = api_client.post(
            f"/api/v1/orders/{order.id}/delivery/assign/",
            {
                "delivery_user_id": str(delivery_user.id),
            },
            format="json",
        )

        assert response.status_code == 400

        assert order.status == OrderStatus.CREATED

        assert not DeliveryAssignment.objects.filter(
            order=order,
        ).exists()

    def test_cannot_create_second_active_assignment(
        self,
        api_client,
        admin_user,
        delivery_user,
        another_delivery_user,
        ready_order,
    ):
        self.authenticate(api_client, admin_user)

        first_response = api_client.post(
            f"/api/v1/orders/{ready_order.id}/delivery/assign/",
            {
                "delivery_user_id": str(delivery_user.id),
            },
            format="json",
        )

        assert first_response.status_code == 201

        second_response = api_client.post(
            f"/api/v1/orders/{ready_order.id}/delivery/assign/",
            {
                "delivery_user_id": str(another_delivery_user.id),
            },
            format="json",
        )

        assert second_response.status_code == 400

        assert (
            DeliveryAssignment.objects.filter(
                order=ready_order,
                status__in=[
                    DeliveryAssignmentStatus.ASSIGNED,
                    DeliveryAssignmentStatus.ACCEPTED,
                ],
            ).count()
            == 1
        )