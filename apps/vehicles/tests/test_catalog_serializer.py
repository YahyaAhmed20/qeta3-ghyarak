import pytest

from apps.vehicles.api.catalog_serializers import (
    VehicleEngineSerializer,
    VehicleGenerationSerializer,
    VehicleMakeSerializer,
    VehicleModelSerializer,
    VehicleVariantSerializer,
)


@pytest.mark.django_db
class TestVehicleCatalogSerializers:

    def test_make_serializer(self, vehicle_variant):
        make = vehicle_variant.engine.generation.model.make

        data = VehicleMakeSerializer(make).data

        assert data == {
            "id": str(make.id),
            "name": make.name,
            "slug": make.slug,
        }

    def test_model_serializer(self, vehicle_variant):
        vehicle_model = vehicle_variant.engine.generation.model

        data = VehicleModelSerializer(vehicle_model).data

        assert data == {
            "id": str(vehicle_model.id),
            "name": vehicle_model.name,
            "slug": vehicle_model.slug,
        }

    def test_generation_serializer(self, vehicle_variant):
        generation = vehicle_variant.engine.generation

        data = VehicleGenerationSerializer(generation).data

        assert data == {
            "id": str(generation.id),
            "name": generation.name,
            "slug": generation.slug,
            "year_from": generation.year_from,
            "year_to": generation.year_to,
        }

    def test_engine_serializer(self, vehicle_variant):
        engine = vehicle_variant.engine

        data = VehicleEngineSerializer(engine).data

        assert data == {
            "id": str(engine.id),
            "name": engine.name,
            "code": engine.code,
            "displacement_cc": engine.displacement_cc,
            "fuel_type": engine.fuel_type,
            "power_hp": engine.power_hp,
        }

    def test_variant_serializer(self, vehicle_variant):
        data = VehicleVariantSerializer(vehicle_variant).data

        assert data == {
            "id": str(vehicle_variant.id),
            "name": vehicle_variant.name,
            "slug": vehicle_variant.slug,
            "transmission": vehicle_variant.transmission,
            "market": vehicle_variant.market,
        }

    def test_catalog_serializers_are_read_only(
        self,
        vehicle_variant,
    ):
        make = vehicle_variant.engine.generation.model.make
        vehicle_model = vehicle_variant.engine.generation.model
        generation = vehicle_variant.engine.generation
        engine = vehicle_variant.engine
        variant = vehicle_variant

        serializers = [
            VehicleMakeSerializer(make),
            VehicleModelSerializer(vehicle_model),
            VehicleGenerationSerializer(generation),
            VehicleEngineSerializer(engine),
            VehicleVariantSerializer(variant),
        ]

        for serializer in serializers:
            assert set(serializer.fields.keys())
            assert all(
                field.read_only
                for field in serializer.fields.values()
            )