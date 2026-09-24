from django.urls import path

from apps.cart.api.views import ActiveCartAPIView


urlpatterns = [
    path("", ActiveCartAPIView.as_view(), name="active-cart"),
]