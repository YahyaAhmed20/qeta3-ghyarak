from django.urls import path

from apps.reviews.api.views import (
    ReviewCreateAPIView,
    ReviewDetailAPIView,
)


urlpatterns = [
    path(
        "",
        ReviewCreateAPIView.as_view(),
        name="review-create",
    ),
    path(
        "<uuid:review_id>/",
        ReviewDetailAPIView.as_view(),
        name="review-detail",
    ),
]