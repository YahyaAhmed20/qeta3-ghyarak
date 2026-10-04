from apps.vehicles.models import (
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)


class VehicleCatalogSelector:

    @staticmethod
    def get_active_makes():
        return VehicleMake.objects.filter(
            is_active=True,
        ).order_by("name")

    @staticmethod
    def get_active_models(*, make_id):
        return VehicleModel.objects.filter(
            make_id=make_id,
            is_active=True,
        ).order_by("name")

    @staticmethod
    def get_active_generations(*, model_id):
        return VehicleGeneration.objects.filter(
            model_id=model_id,
            is_active=True,
        ).order_by("year_from", "name")

    @staticmethod
    def get_active_engines(*, generation_id):
        return VehicleEngine.objects.filter(
            generation_id=generation_id,
            is_active=True,
        ).order_by("name")

    @staticmethod
    def get_active_variants(*, engine_id):
        return VehicleVariant.objects.filter(
            engine_id=engine_id,
            is_active=True,
        ).order_by("name")