from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.vehicles.api.serializers import (
    CustomerVehicleCreateSerializer,
    CustomerVehicleSerializer,
    CustomerVehicleUpdateSerializer,
)
from apps.vehicles.selectors.customer_vehicle import CustomerVehicleSelector
from apps.vehicles.services.customer_vehicle import CustomerVehicleService


class CustomerVehicleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vehicles = CustomerVehicleSelector.get_customer_vehicles(
            customer=request.user,
        )

        serializer = CustomerVehicleSerializer(
            vehicles,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = CustomerVehicleCreateSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        try:
            vehicle = CustomerVehicleService.add_vehicle(
                customer=request.user,
                **serializer.validated_data,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = CustomerVehicleSerializer(vehicle)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class CustomerVehicleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, vehicle_id):
        return CustomerVehicleSelector.get_customer_vehicle(
            customer=request.user,
            vehicle_id=vehicle_id,
        )

    def get(self, request, vehicle_id):
        vehicle = self.get_object(request, vehicle_id)

        if vehicle is None:
            return Response(
                {"detail": "Vehicle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerVehicleSerializer(vehicle)

        return Response(serializer.data)

    def patch(self, request, vehicle_id):
        vehicle = self.get_object(request, vehicle_id)

        if vehicle is None:
            return Response(
                {"detail": "Vehicle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerVehicleUpdateSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        try:
            vehicle = CustomerVehicleService.update_vehicle(
                customer=request.user,
                vehicle_id=vehicle_id,
                **serializer.validated_data,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = CustomerVehicleSerializer(vehicle)

        return Response(response_serializer.data)

    def delete(self, request, vehicle_id):
        vehicle = self.get_object(request, vehicle_id)

        if vehicle is None:
            return Response(
                {"detail": "Vehicle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            CustomerVehicleService.remove_vehicle(
                customer=request.user,
                vehicle_id=vehicle_id,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class CustomerVehicleSetDefaultAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, vehicle_id):
        vehicle = CustomerVehicleSelector.get_customer_vehicle(
            customer=request.user,
            vehicle_id=vehicle_id,
        )

        if vehicle is None:
            return Response(
                {"detail": "Vehicle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            vehicle = CustomerVehicleService.set_default(
                customer=request.user,
                vehicle_id=vehicle_id,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CustomerVehicleSerializer(vehicle)

        return Response(serializer.data)