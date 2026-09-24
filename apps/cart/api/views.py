from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.api.serializers import CartSerializer
from apps.cart.selectors.cart import CartSelector


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