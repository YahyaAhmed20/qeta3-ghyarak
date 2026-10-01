from apps.vehicles.models import CustomerVehicle


class CustomerVehicleSelector:

    @staticmethod
    def get_customer_vehicles(*, customer):
        return (
            CustomerVehicle.objects
            .filter(customer=customer)
            .select_related(
                "vehicle_variant",
                "vehicle_variant__engine",
                "vehicle_variant__engine__generation",
                "vehicle_variant__engine__generation__model",
                "vehicle_variant__engine__generation__model__make",
            )
        )

    @staticmethod
    def get_customer_vehicle(*, customer, vehicle_id):
        return (
            CustomerVehicle.objects
            .filter(
                id=vehicle_id,
                customer=customer,
            )
            .select_related(
                "vehicle_variant",
                "vehicle_variant__engine",
                "vehicle_variant__engine__generation",
                "vehicle_variant__engine__generation__model",
                "vehicle_variant__engine__generation__model__make",
            )
            .first()
        )

    @staticmethod
    def get_default_vehicle(*, customer):
        return (
            CustomerVehicle.objects
            .filter(
                customer=customer,
                is_default=True,
            )
            .select_related(
                "vehicle_variant",
                "vehicle_variant__engine",
                "vehicle_variant__engine__generation",
                "vehicle_variant__engine__generation__model",
                "vehicle_variant__engine__generation__model__make",
            )
            .first()
        )