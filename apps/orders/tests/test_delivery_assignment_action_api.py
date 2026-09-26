import pytest
from rest_framework.test import APIClient

from apps.orders.constants import (
    DeliveryAssignmentStatus,
    OrderStatus,
)
from apps.orders.models import DeliveryAssignment
from apps.orders.services.delivery_assignment import DeliveryAssignmentService
from apps.orders.services.order import OrderService


@pytest.mark.django_db
class TestDeliveryAssignmentActionAPI:

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

    def create_assignment(
        self,
        ready_order,
        admin_user,
        delivery_user,
    ):
        return DeliveryAssignmentService.assign(
            order_id=ready_order.id,
            delivery_user=delivery_user,
            actor=admin_user,
        )

    def test_assigned_delivery_can_accept(
        self,
        api_client,
        delivery_user,
        admin_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, delivery_user)

        response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/accept/",
            format="json",
        )

        assert response.status_code == 200

        assignment.refresh_from_db()

        assert assignment.status == DeliveryAssignmentStatus.ACCEPTED
        assert assignment.accepted_at is not None

        assert response.data["status"] == DeliveryAssignmentStatus.ACCEPTED

    def test_another_delivery_cannot_accept(
        self,
        api_client,
        delivery_user,
        another_delivery_user,
        admin_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, another_delivery_user)

        response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/accept/",
            format="json",
        )

        assert response.status_code == 403

        assignment.refresh_from_db()

        assert assignment.status == DeliveryAssignmentStatus.ASSIGNED

    def test_non_delivery_cannot_accept(
        self,
        api_client,
        seller_owner,
        delivery_user,
        admin_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, seller_owner)

        response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/accept/",
            format="json",
        )

        assert response.status_code == 403

    def test_assignment_cannot_be_accepted_twice(
        self,
        api_client,
        delivery_user,
        admin_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, delivery_user)

        first_response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/accept/",
            format="json",
        )

        assert first_response.status_code == 200

        second_response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/accept/",
            format="json",
        )

        assert second_response.status_code == 400

        assignment.refresh_from_db()

        assert assignment.status == DeliveryAssignmentStatus.ACCEPTED

    def test_assigned_delivery_can_cancel(
        self,
        api_client,
        delivery_user,
        admin_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, delivery_user)

        response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/cancel/",
            format="json",
        )

        assert response.status_code == 200

        assignment.refresh_from_db()

        assert assignment.status == DeliveryAssignmentStatus.CANCELLED

    def test_admin_can_cancel(
        self,
        api_client,
        admin_user,
        delivery_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, admin_user)

        response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/cancel/",
            format="json",
        )

        assert response.status_code == 200

        assignment.refresh_from_db()

        assert assignment.status == DeliveryAssignmentStatus.CANCELLED

    def test_unrelated_user_cannot_cancel(
        self,
        api_client,
        seller_owner,
        delivery_user,
        admin_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, seller_owner)

        response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/cancel/",
            format="json",
        )

        assert response.status_code == 403

        assignment.refresh_from_db()

        assert assignment.status == DeliveryAssignmentStatus.ASSIGNED

    def test_cancelled_assignment_cannot_be_cancelled_again(
        self,
        api_client,
        delivery_user,
        admin_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, delivery_user)

        first_response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/cancel/",
            format="json",
        )

        assert first_response.status_code == 200

        second_response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/cancel/",
            format="json",
        )

        assert second_response.status_code == 400

        assignment.refresh_from_db()

        assert assignment.status == DeliveryAssignmentStatus.CANCELLED

    def test_cancelled_assignment_cannot_be_accepted(
        self,
        api_client,
        delivery_user,
        admin_user,
        ready_order,
    ):
        assignment = self.create_assignment(
            ready_order,
            admin_user,
            delivery_user,
        )

        self.authenticate(api_client, delivery_user)

        cancel_response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/cancel/",
            format="json",
        )

        assert cancel_response.status_code == 200

        accept_response = api_client.post(
            f"/api/v1/orders/delivery/assignments/"
            f"{assignment.id}/accept/",
            format="json",
        )

        assert accept_response.status_code == 400

        assignment.refresh_from_db()

        assert assignment.status == DeliveryAssignmentStatus.CANCELLED