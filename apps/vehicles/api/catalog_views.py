from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny

from apps.vehicles.api.catalog_serializers import (
    VehicleEngineSerializer,
    VehicleGenerationSerializer,
    VehicleMakeSerializer,
    VehicleModelSerializer,
    VehicleVariantSerializer,
)
from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
)
from apps.vehicles.selectors.catalog import VehicleCatalogSelector


class VehicleMakeListAPIView(generics.ListAPIView):
    serializer_class = VehicleMakeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return VehicleCatalogSelector.get_active_makes()


class VehicleModelListAPIView(generics.ListAPIView):
    serializer_class = VehicleModelSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        make = VehicleMake.objects.filter(
            id=self.kwargs["make_id"],
            is_active=True,
        ).first()

        if make is None:
            raise NotFound("Vehicle make not found.")

        return VehicleCatalogSelector.get_active_models(
            make_id=make.id,
        )


class VehicleGenerationListAPIView(generics.ListAPIView):
    serializer_class = VehicleGenerationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        vehicle_model = VehicleModel.objects.filter(
            id=self.kwargs["model_id"],
            is_active=True,
        ).first()

        if vehicle_model is None:
            raise NotFound("Vehicle model not found.")

        return VehicleCatalogSelector.get_active_generations(
            model_id=vehicle_model.id,
        )


class VehicleEngineListAPIView(generics.ListAPIView):
    serializer_class = VehicleEngineSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        generation = VehicleGeneration.objects.filter(
            id=self.kwargs["generation_id"],
            is_active=True,
        ).first()

        if generation is None:
            raise NotFound("Vehicle generation not found.")

        return VehicleCatalogSelector.get_active_engines(
            generation_id=generation.id,
        )


class VehicleVariantListAPIView(generics.ListAPIView):
    serializer_class = VehicleVariantSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        engine = VehicleEngine.objects.filter(
            id=self.kwargs["engine_id"],
            is_active=True,
        ).first()

        if engine is None:
            raise NotFound("Vehicle engine not found.")

        return VehicleCatalogSelector.get_active_variants(
            engine_id=engine.id,
        )