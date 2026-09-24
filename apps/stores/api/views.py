from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.stores.api.serializers import (
    SellerProductSerializer,
    StoreSerializer,
)
from apps.stores.models import SellerProduct, Store, StoreStatus
from apps.stores.services.seller_product import SellerProductService


class StoreCreateAPIView(generics.CreateAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]


class MyStoreListAPIView(generics.ListAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Store.objects
            .filter(owner=self.request.user)
            .order_by("name")
        )


class MyStoreDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Store.objects.filter(
            owner=self.request.user,
        )


class SellerProductListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SellerProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            SellerProduct.objects
            .filter(store__owner=self.request.user)
            .select_related(
                "store",
                "product",
                "product__category",
                "product__brand",
            )
        )

        is_active = self.request.query_params.get("is_active")

        if is_active == "true":
            queryset = queryset.filter(is_active=True)
        elif is_active == "false":
            queryset = queryset.filter(is_active=False)

        return queryset.order_by("product__name")

    def get_store(self):
        store = (
            Store.objects
            .filter(
                owner=self.request.user,
                status=StoreStatus.ACTIVE,
                is_verified=True,
            )
            .first()
        )

        if store is None:
            raise ValidationError(
                {"detail": "You do not have an active verified store."}
            )

        return store

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["store"] = self.get_store()
        return context


class SellerProductDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = SellerProductSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return SellerProduct.objects.filter(
            store__owner=self.request.user,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["store"] = self.get_object().store
        return context

    def update(self, request, *args, **kwargs):
        seller_product = self.get_object()

        serializer = self.get_serializer(
            seller_product,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        try:
            seller_product = SellerProductService.update_seller_product(
                seller_product_id=seller_product.id,
                store=seller_product.store,
                **serializer.validated_data,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        output_serializer = self.get_serializer(seller_product)

        return Response(
            output_serializer.data,
            status=200,
        )


class SellerProductDeactivateAPIView(generics.GenericAPIView):
    serializer_class = SellerProductSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return SellerProduct.objects.filter(
            store__owner=self.request.user,
        )

    def patch(self, request, *args, **kwargs):
        seller_product = self.get_object()

        try:
            SellerProductService.deactivate_seller_product(
                seller_product_id=seller_product.id,
                store=seller_product.store,
            )
        except ValueError as exc:
            raise ValidationError(
                {"detail": str(exc)}
            ) from exc

        seller_product.refresh_from_db()

        return Response(
            SellerProductSerializer(
                seller_product,
                context=self.get_serializer_context(),
            ).data
        )


class SellerProductActivateAPIView(generics.GenericAPIView):
    serializer_class = SellerProductSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return SellerProduct.objects.filter(
            store__owner=self.request.user,
        )

    def patch(self, request, *args, **kwargs):
        seller_product = self.get_object()

        try:
            SellerProductService.activate_seller_product(
                seller_product_id=seller_product.id,
                store=seller_product.store,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        seller_product.refresh_from_db()

        return Response(
            SellerProductSerializer(
                seller_product,
                context=self.get_serializer_context(),
            ).data
        )