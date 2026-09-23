from django.db import transaction

from apps.vehicles.models import CustomerVehicle
from apps.common.normalizers import normalize_vin

class CustomerVehicleService:

    @staticmethod
    @transaction.atomic
    def add_vehicle(
        *,
        customer,
        vehicle_variant,
        nickname="",
        plate_number="",
        vin="",
    ):
        if not vehicle_variant.is_active:
            raise ValueError("Vehicle variant is not active.")

        if CustomerVehicle.objects.filter(
            customer=customer,
            vehicle_variant=vehicle_variant,
        ).exists():
            raise ValueError(
                "Customer already has this vehicle."
            )

        has_default_vehicle = CustomerVehicle.objects.filter(
            customer=customer,
            is_default=True,
        ).exists()

        normalized_vin = normalize_vin(vin)

        vehicle = CustomerVehicle(
            customer=customer,
            vehicle_variant=vehicle_variant,
            nickname=nickname,
            plate_number=plate_number,
            vin=normalized_vin,
            is_default=not has_default_vehicle,
        )

        vehicle.full_clean()
        vehicle.save()

        return vehicle

    @staticmethod
    @transaction.atomic
    def set_default(
        *,
        customer,
        vehicle_id,
    ):
        vehicle = (
            CustomerVehicle.objects
            .select_for_update()
            .filter(
                id=vehicle_id,
                customer=customer,
            )
            .first()
        )

        if vehicle is None:
            raise ValueError(
                "Customer vehicle not found."
            )

        if vehicle.is_default:
            return vehicle

        (
            CustomerVehicle.objects
            .select_for_update()
            .filter(
                customer=customer,
                is_default=True,
            )
            .update(is_default=False)
        )

        vehicle.is_default = True
        vehicle.save(
            update_fields=[
                "is_default",
                "updated_at",
            ]
        )

        return vehicle

    @staticmethod
    @transaction.atomic
    def remove_vehicle(
        *,
        customer,
        vehicle_id,
    ):
        vehicle = (
            CustomerVehicle.objects
            .select_for_update()
            .filter(
                id=vehicle_id,
                customer=customer,
            )
            .first()
        )

        if vehicle is None:
            raise ValueError(
                "Customer vehicle not found."
            )

        was_default = vehicle.is_default

        vehicle.delete()

        if was_default:
            next_vehicle = (
                CustomerVehicle.objects
                .select_for_update()
                .filter(customer=customer)
                .order_by("-created_at")
                .first()
            )

            if next_vehicle is not None:
                next_vehicle.is_default = True
                next_vehicle.save(
                    update_fields=[
                        "is_default",
                        "updated_at",
                    ]
                )

    @staticmethod
    @transaction.atomic
    def update_vehicle(
        *,
        customer,
        vehicle_id,
        nickname=None,
        plate_number=None,
        vin=None,
    ):
        vehicle = (
            CustomerVehicle.objects
            .select_for_update()
            .filter(
                id=vehicle_id,
                customer=customer,
            )
            .first()
        )

        if vehicle is None:
            raise ValueError(
                "Customer vehicle not found."
            )

        if nickname is not None:
            vehicle.nickname = nickname

        if plate_number is not None:
            vehicle.plate_number = plate_number

        if vin is not None:
            vehicle.vin = normalize_vin(vin)

        vehicle.full_clean(
            exclude=["customer", "vehicle_variant"]
        )

        vehicle.save()

        return vehicle