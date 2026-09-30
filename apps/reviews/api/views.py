from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reviews.api.serializers import ReviewSerializer
from apps.reviews.models import Review
from apps.reviews.services.review import ReviewService


class ReviewCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = UUID(str(request.data.get("order")))
        store_id = UUID(str(request.data.get("store_id")))

        product_id = request.data.get("product_id")
        if product_id:
            product_id = UUID(str(product_id))

        rating = request.data.get("rating")
        comment = request.data.get("comment", "")

        try:
            review = ReviewService.create(
                order_id=order_id,
                customer=request.user,
                store_id=store_id,
                product_id=product_id,
                rating=rating,
                comment=comment,
            )

        except (ValueError, DjangoValidationError) as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class ReviewDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, review_id):
        review = get_object_or_404(
            Review.objects.select_related(
                "customer",
                "store",
                "product",
                "order",
            ),
            id=review_id,
        )

        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_200_OK,
        )