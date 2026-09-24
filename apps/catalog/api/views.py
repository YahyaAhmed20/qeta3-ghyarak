from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from apps.catalog.api.part_number_serializers import (
    ProductPartNumberSerializer,
)
from apps.catalog.api.serializers import (
    ProductCompatibilitySerializer,
    ProductSerializer,
)
from apps.catalog.models import (
    ProductCompatibility,
    ProductPartNumber,
    CompatibilityStatus,

)
from apps.catalog.selectors.compatibility import CompatibilitySelector
from apps.catalog.selectors.product import ProductSelector
from apps.catalog.services.compatibility import CompatibilityService


class ProductListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = ProductListPagination

    def get_queryset(self):
        return ProductSelector.get_active_products()


class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"

    def get_queryset(self):
        return ProductSelector.get_active_products()


class ProductPartNumberListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductPartNumberListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ProductPartNumberSerializer
    permission_classes = [AllowAny]
    pagination_class = ProductPartNumberListPagination

    def get_queryset(self):
        return (
            ProductPartNumber.objects
            .filter(is_active=True)
            .select_related("product", "brand")
        )


class ProductPartNumberDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ProductPartNumberSerializer
    permission_classes = [AllowAny]

    lookup_field = "id"

    def get_queryset(self):
        return (
            ProductPartNumber.objects
            .filter(is_active=True)
            .select_related("product", "brand")
        )


class ProductCompatibilityListAPIView(generics.ListAPIView):
    serializer_class = ProductCompatibilitySerializer
    permission_classes = [AllowAny]
    pagination_class = ProductListPagination

    def get_queryset(self):
        return CompatibilitySelector.get_approved_for_product(
            product_id=self.kwargs["product_id"],
        )


class ProductCompatibilityDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductCompatibilitySerializer
    permission_classes = [AllowAny]
    lookup_field = "id"

    def get_queryset(self):
        return ProductCompatibility.objects.filter(
            id=self.kwargs["id"],
            status=CompatibilityStatus.APPROVED,
            product__is_active=True,
            vehicle_variant__is_active=True,
        ).select_related(
            "product",
            "product__category",
            "product__brand",
            "vehicle_variant",
            "vehicle_variant__engine",
            "vehicle_variant__engine__generation",
            "vehicle_variant__engine__generation__model",
            "vehicle_variant__engine__generation__model__make",
        )