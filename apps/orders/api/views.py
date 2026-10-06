from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.addresses.selectors import AddressSelector
from apps.cart.models import Cart
from apps.cart.selectors import CartSelector
from apps.orders.services.order import OrderService
from apps.orders.constants import DeliveryAssignmentStatus
from apps.orders.models import DeliveryAssignment
from apps.orders.services.delivery_assignment import (
    DeliveryAssignmentService,
)
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.orders.api.serializers import SellerOrderSerializer
from apps.orders.selectors.order import OrderSelector
from apps.stores.models import Store

from apps.orders.api.serializers import (
    DeliveryAssignmentCreateSerializer,
)


from apps.orders.api.serializers import (
    DeliveryAssignmentCreateSerializer,
    CheckoutSerializer,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.addresses.selectors import AddressSelector
from apps.cart.selectors import CartSelector
from apps.orders.services.order import OrderService
from apps.orders.api.serializers import CheckoutSerializer
from apps.orders.models import Order


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
        
class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only customers can checkout."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        address_id = serializer.validated_data["address_id"]
        notes = serializer.validated_data.get("notes", "")

        address = AddressSelector.get_address(
            address_id=address_id,
        )

        if address is None:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if address.customer_id != request.user.id:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart = CartSelector.get_active_cart_for_customer(
            customer_id=request.user.id,
        )

        if cart is None:
            return Response(
                {"detail": "Active cart not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        address_snapshot = {
            "label": address.label,
            "recipient_name": address.recipient_name,
            "phone": address.phone,
            "city": address.city,
            "area": address.area,
            "address_line": address.address_line,
            "building": address.building,
            "floor": address.floor,
            "apartment": address.apartment,
            "landmark": address.landmark,
            "latitude": (
                str(address.latitude)
                if address.latitude is not None
                else None
            ),
            "longitude": (
                str(address.longitude)
                if address.longitude is not None
                else None
            ),
        }

        try:
            order = OrderService.create_order(
                customer=request.user,
                cart=cart,
                address_snapshot=address_snapshot,
                notes=notes,
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
                "subtotal": str(order.subtotal),
                "delivery_fee": str(order.delivery_fee),
                "total": str(order.total),
            },
            status=status.HTTP_201_CREATED,
        )
        
        
class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only customers can checkout."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        address = AddressSelector.get_address(
            address_id=serializer.validated_data["address_id"]
        )

        if address is None:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if address.customer_id != request.user.id:
            return Response(
                {"detail": "Address not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart = CartSelector.get_active_cart_for_customer(
            customer=request.user
        )

        if cart is None:
            return Response(
                {"detail": "No active cart found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        address_snapshot = {
            "label": address.label,
            "recipient_name": address.recipient_name,
            "phone": address.phone,
            "city": address.city,
            "area": address.area,
            "address_line": address.address_line,
            "building": address.building,
            "floor": address.floor,
            "apartment": address.apartment,
            "landmark": address.landmark,
            "latitude": str(address.latitude) if address.latitude is not None else None,
            "longitude": str(address.longitude) if address.longitude is not None else None,
        }

        try:
            order = OrderService.create_order(
                customer=request.user,
                cart=cart,
                address_snapshot=address_snapshot,
                notes=serializer.validated_data.get("notes", ""),
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
                "subtotal": str(order.subtotal),
                "delivery_fee": str(order.delivery_fee),
                "total": str(order.total),
            },
            status=status.HTTP_201_CREATED,
        )
        
    
class OrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only customers can view orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        orders = (
            Order.objects
            .filter(customer=request.user)
            .order_by("-created_at")
        )

        return Response(
            {
                "count": orders.count(),
                "results": [
                    {
                        "id": str(order.id),
                        "order_number": order.order_number,
                        "status": order.status,
                        "subtotal": str(order.subtotal),
                        "delivery_fee": str(order.delivery_fee),
                        "total": str(order.total),
                        "created_at": order.created_at,
                    }
                    for order in orders
                ],
            },
            status=status.HTTP_200_OK,
        )
        
class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        if request.user.role != "CUSTOMER":
            return Response(
                {"detail": "Only customers can view orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = (
            Order.objects
            .filter(
                id=order_id,
                customer=request.user,
            )
            .prefetch_related("items")
            .first()
        )

        if order is None:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
                "subtotal": str(order.subtotal),
                "seller_discount": str(order.seller_discount),
                "platform_discount": str(order.platform_discount),
                "delivery_fee": str(order.delivery_fee),
                "total": str(order.total),
                "address_snapshot": order.address_snapshot,
                "notes": order.notes,
                "delivered_at": order.delivered_at,
                "created_at": order.created_at,
                "items": [
                    {
                        "id": str(item.id),
                        "product_name": item.product_name_snapshot,
                        "part_number": item.part_number_snapshot,
                        "unit_price": str(item.unit_price),
                        "discount": str(item.discount),
                        "quantity": item.quantity,
                        "subtotal": str(item.subtotal),
                    }
                    for item in order.items.all()
                ],
            },
            status=status.HTTP_200_OK,
        )
        
        
class SellerOrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "SELLER_OWNER":
            return Response(
                {"detail": "Only sellers can view store orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        orders = (
            Order.objects
            .filter(store__owner=request.user)
            .order_by("-created_at")
        )

        return Response(
            {
                "count": orders.count(),
                "results": [
                    {
                        "id": str(order.id),
                        "order_number": order.order_number,
                        "status": order.status,
                        "total": str(order.total),
                        "created_at": order.created_at,
                    }
                    for order in orders
                ],
            },
            status=status.HTTP_200_OK,
        )
        
        
class SellerOrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        store = (
            Store.objects
            .filter(
                owner=request.user,
                status="ACTIVE",
                is_verified=True,
            )
            .first()
        )

        if not store:
            return Response(
                {"detail": "You do not have an active verified store."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = OrderSelector.get_store_order(
            store=store,
            order_id=order_id,
        )

        if order is None:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SellerOrderSerializer(order)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
        
        
class SellerOrderAcceptAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        if request.user.role not in {
            "SELLER_OWNER",
            "SELLER_MANAGER",
            "SELLER_STAFF",
        }:
            return Response(
                {"detail": "Only sellers can accept orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            order = OrderService.transition_status(
                order_id=order_id,
                new_status="ACCEPTED",
                actor=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )
        
        
class SellerOrderPreparingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        if request.user.role not in {
            "SELLER_OWNER",
            "SELLER_MANAGER",
            "SELLER_STAFF",
        }:
            return Response(
                {"detail": "Only sellers can prepare orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            order = OrderService.transition_status(
                order_id=order_id,
                new_status="PREPARING",
                actor=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )
        
class SellerOrderReadyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        if request.user.role not in {
            "SELLER_OWNER",
            "SELLER_MANAGER",
            "SELLER_STAFF",
        }:
            return Response(
                {"detail": "Only sellers can mark orders as ready."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            order = OrderService.transition_status(
                order_id=order_id,
                new_status="READY",
                actor=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )
        
class SellerOrderOutForDeliveryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        if request.user.role not in {
            "SELLER_OWNER",
            "SELLER_MANAGER",
            "SELLER_STAFF",
        }:
            return Response(
                {"detail": "Only sellers can send orders for delivery."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            order = OrderService.transition_status(
                order_id=order_id,
                new_status="OUT_FOR_DELIVERY",
                actor=request.user,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": str(order.id),
                "order_number": order.order_number,
                "status": order.status,
            },
            status=status.HTTP_200_OK,
        )
        
        
    
class SellerOrderListAPIView(ListAPIView):
    serializer_class = SellerOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        store = (
            Store.objects
            .filter(
                owner=self.request.user,
                status="ACTIVE",
                is_verified=True,
            )
            .first()
        )

        print("REQUEST USER:", self.request.user)
        print("REQUEST USER ID:", self.request.user.id)
        print("REQUEST USER PHONE:", self.request.user.phone)
        print("STORE:", store)
        print("STORE ID:", store.id if store else None)

        if not store:
            return []

        return OrderSelector.get_store_orders(store=store)