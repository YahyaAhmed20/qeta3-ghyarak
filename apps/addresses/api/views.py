from django.core.exceptions import ValidationError

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.addresses.api.serializers import (
    AddressCreateSerializer,
    AddressSerializer,
    AddressUpdateSerializer,
)
from apps.addresses.selectors import AddressSelector
from apps.addresses.services import AddressService


class AddressListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = AddressSelector.get_customer_addresses(
            customer_id=request.user.id,
        )

        return Response(
            AddressSerializer(addresses, many=True).data,
            status=200,
        )

    def post(self, request):
        serializer = AddressCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        address = AddressService.create(
            customer=request.user,
            **serializer.validated_data,
        )

        return Response(
            AddressSerializer(address).data,
            status=201,
        )


class AddressDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, address_id):
        address = AddressSelector.get_address(
            address_id=address_id,
        )

        if address is None or address.customer_id != request.user.id:
            return Response(
                {"detail": "Address not found."},
                status=404,
            )

        return Response(
            AddressSerializer(address).data,
            status=200,
        )

    def patch(self, request, address_id):
        address = AddressSelector.get_address(
            address_id=address_id,
        )

        if address is None or address.customer_id != request.user.id:
            return Response(
                {"detail": "Address not found."},
                status=404,
            )

        serializer = AddressUpdateSerializer(
            address,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        try:
            address = AddressService.update(
                address=address,
                **serializer.validated_data,
            )

        except (ValueError, ValidationError) as exc:
            return Response(
                {"detail": str(exc)},
                status=400,
            )

        return Response(
            AddressSerializer(address).data,
            status=200,
        )

    def delete(self, request, address_id):
        address = AddressSelector.get_address(
            address_id=address_id,
        )

        if address is None or address.customer_id != request.user.id:
            return Response(
                {"detail": "Address not found."},
                status=404,
            )

        AddressService.delete(address=address)

        return Response(
            status=204,
        )