from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Product
from apps.favorites.api.serializers import FavoriteSerializer
from apps.favorites.selectors.favorite import FavoriteSelector
from apps.favorites.services.favorite import FavoriteService


class FavoriteListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = FavoriteSelector.get_customer_favorites(
            customer=request.user,
        )

        serializer = FavoriteSerializer(
            favorites,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get("product")

        if not product_id:
            return Response(
                {"detail": "Product is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        already_exists = FavoriteSelector.is_favorite(
            customer=request.user,
            product=product,
        )

        favorite = FavoriteService.add_favorite(
            customer=request.user,
            product=product,
        )

        serializer = FavoriteSerializer(favorite)

        return Response(
            serializer.data,
            status=(
                status.HTTP_200_OK
                if already_exists
                else status.HTTP_201_CREATED
            ),
        )


class FavoriteDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        product = Product.objects.filter(id=product_id).first()

        if product is None:
            return Response(
                {"detail": "Favorite not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted = FavoriteService.remove_favorite(
            customer=request.user,
            product=product,
        )

        if not deleted:
            return Response(
                {"detail": "Favorite not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        product = Product.objects.filter(id=product_id).first()

        if product is None:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_favorite = FavoriteSelector.is_favorite(
            customer=request.user,
            product=product,
        )

        return Response(
            {"is_favorite": is_favorite},
            status=status.HTTP_200_OK,
        )