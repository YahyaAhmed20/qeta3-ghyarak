from django.urls import path

from apps.favorites.api.views import (
    FavoriteCheckAPIView,
    FavoriteDeleteAPIView,
    FavoriteListCreateAPIView,
)

urlpatterns = [
    path(
        "",
        FavoriteListCreateAPIView.as_view(),
        name="favorite-list-create",
    ),
    path(
        "check/<uuid:product_id>/",
        FavoriteCheckAPIView.as_view(),
        name="favorite-check",
    ),
    path(
        "<uuid:product_id>/",
        FavoriteDeleteAPIView.as_view(),
        name="favorite-delete",
    ),
]