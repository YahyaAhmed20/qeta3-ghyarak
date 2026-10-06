from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.api.serializers import (
    CartItemWriteSerializer,
    CartItemQuantitySerializer,
    CartSerializer,
)
from apps.cart.selectors.cart import CartSelector
from apps.cart.services.cart import CartService
from apps.cart.services.cart_item import CartItemService
from apps.stores.models import SellerProduct


class ActiveCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = CartSelector.get_active_cart_for_customer(
            customer=request.user
        )

        if cart is None:
            return Response({"cart": None})

        return Response({
            "cart": CartSerializer(cart).data
        })


class CartItemCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CartItemWriteSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        seller_product = (
            SellerProduct.objects
            .select_related("store")
            .filter(
                id=serializer.validated_data["seller_product_id"],
            )
            .first()
        )

        if seller_product is None:
            return Response(
                {"detail": "Seller product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            cart, _ = CartService.get_or_create_active_cart(
                customer=request.user,
                store=seller_product.store,
            )

            CartItemService.add_item(
                cart=cart,
                seller_product=seller_product,
                quantity=serializer.validated_data["quantity"],
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = CartSelector.get_active_cart_for_customer(
            customer=request.user
        )

        return Response(
            {
                "cart": CartSerializer(cart).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CartItemUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        cart = CartSelector.get_active_cart_for_customer(
            customer=request.user
        )

        if cart is None:
            return Response(
                {"detail": "Active cart not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CartItemQuantitySerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        try:
            CartItemService.update_quantity(
                cart=cart,
                item_id=item_id,
                quantity=serializer.validated_data["quantity"],
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart = CartSelector.get_active_cart_for_customer(
            customer=request.user
        )

        return Response({
            "cart": CartSerializer(cart).data
        })

    def delete(self, request, item_id):
        cart = CartSelector.get_active_cart_for_customer(
            customer=request.user
        )

        if cart is None:
            return Response(
                {"detail": "Active cart not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            CartItemService.remove_item(
                cart=cart,
                item_id=item_id,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
        
        
class CartClearAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = CartSelector.get_active_cart_for_customer(
            customer=request.user
        )

        if cart is None:
            return Response(
                {"detail": "Active cart not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        CartItemService.clear_cart(cart=cart)

        return Response(
            {"detail": "Cart cleared successfully."},
            status=status.HTTP_200_OK,
        )