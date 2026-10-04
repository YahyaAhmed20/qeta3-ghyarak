import pytest

from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)
from apps.vehicles.selectors.catalog import VehicleCatalogSelector


@pytest.mark.django_db
class TestVehicleCatalogSelector:

    def test_get_active_makes_returns_only_active_makes(
        self,
        vehicle_variant,
    ):
        active_make = vehicle_variant.engine.generation.model.make

        inactive_make = VehicleMake.objects.create(
            name="Inactive Make",
            slug="inactive-make",
            is_active=False,
        )

        makes = VehicleCatalogSelector.get_active_makes()

        assert active_make in makes
        assert inactive_make not in makes

    def test_get_active_models_returns_only_models_for_make(
        self,
        vehicle_variant,
    ):
        make = vehicle_variant.engine.generation.model.make

        active_model = vehicle_variant.engine.generation.model

        other_make = VehicleMake.objects.create(
            name="BMW",
            slug="bmw",
        )

        other_model = VehicleModel.objects.create(
            make=other_make,
            name="3 Series",
            slug="3-series",
        )

        inactive_model = VehicleModel.objects.create(
            make=make,
            name="Inactive Model",
            slug="inactive-model",
            is_active=False,
        )

        models = VehicleCatalogSelector.get_active_models(
            make_id=make.id,
        )

        assert active_model in models
        assert other_model not in models
        assert inactive_model not in models

    def test_get_active_generations_returns_only_generations_for_model(
        self,
        vehicle_variant,
    ):
        model = vehicle_variant.engine.generation.model

        active_generation = vehicle_variant.engine.generation

        inactive_generation = VehicleGeneration.objects.create(
            model=model,
            name="Inactive Generation",
            slug="inactive-generation",
            is_active=False,
        )

        other_make = VehicleMake.objects.create(
            name="BMW",
            slug="bmw",
        )

        other_model = VehicleModel.objects.create(
            make=other_make,
            name="3 Series",
            slug="3-series",
        )

        other_generation = VehicleGeneration.objects.create(
            model=other_model,
            name="G20",
            slug="g20",
        )

        generations = VehicleCatalogSelector.get_active_generations(
            model_id=model.id,
        )

        assert active_generation in generations
        assert inactive_generation not in generations
        assert other_generation not in generations

    def test_get_active_engines_returns_only_engines_for_generation(
        self,
        vehicle_variant,
    ):
        generation = vehicle_variant.engine.generation

        active_engine = vehicle_variant.engine

        inactive_engine = VehicleEngine.objects.create(
            generation=generation,
            name="Inactive Engine",
            code="INACTIVE",
            is_active=False,
        )

        engines = VehicleCatalogSelector.get_active_engines(
            generation_id=generation.id,
        )

        assert active_engine in engines
        assert inactive_engine not in engines

    def test_get_active_variants_returns_only_variants_for_engine(
        self,
        vehicle_variant,
    ):
        engine = vehicle_variant.engine

        active_variant = vehicle_variant

        inactive_variant = VehicleVariant.objects.create(
            engine=engine,
            name="Inactive Variant",
            slug="inactive-variant",
            is_active=False,
        )

        variants = VehicleCatalogSelector.get_active_variants(
            engine_id=engine.id,
        )

        assert active_variant in variants
        assert inactive_variant not in variants

    def test_catalog_selectors_return_empty_for_unknown_parent(
        self,
    ):
        unknown_id = "00000000-0000-0000-0000-000000000000"

        assert not VehicleCatalogSelector.get_active_models(
            make_id=unknown_id,
        ).exists()

        assert not VehicleCatalogSelector.get_active_generations(
            model_id=unknown_id,
        ).exists()

        assert not VehicleCatalogSelector.get_active_engines(
            generation_id=unknown_id,
        ).exists()

        assert not VehicleCatalogSelector.get_active_variants(
            engine_id=unknown_id,
        ).exists()