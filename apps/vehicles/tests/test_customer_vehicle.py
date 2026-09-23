import pytest
from django.db import IntegrityError

from apps.accounts.models import User
from apps.vehicles.models import (
    CustomerVehicle,
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)


@pytest.mark.django_db
class TestCustomerVehicle:

    def setup_vehicle_variant(self):
        make = VehicleMake.objects.create(
            name="Skoda",
            slug="skoda",
        )

        model = VehicleModel.objects.create(
            make=make,
            name="Octavia",
            slug="octavia",
        )

        generation = VehicleGeneration.objects.create(
            model=model,
            name="A5",
            slug="a5",
            year_from=2004,
            year_to=2013,
        )

        engine = VehicleEngine.objects.create(
            generation=generation,
            name="1.6 MPI",
            code="BSE",
            displacement_cc=1595,
            fuel_type="PETROL",
            power_hp=102,
        )

        variant = VehicleVariant.objects.create(
            engine=engine,
            name="1.6 MPI Manual",
            slug="1-6-mpi-manual",
            transmission="MANUAL",
            market="EGYPT",
        )

        return variant

    def create_customer(self, phone):
        return User.objects.create_user(
            phone=phone,
            password="TestPassword123!",
            role="CUSTOMER",
        )

    def test_create_customer_vehicle(self):
        customer = self.create_customer("+201000000001")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicle.objects.create(
            customer=customer,
            vehicle_variant=variant,
            nickname="My Octavia",
            plate_number="س ص 1234",
            vin="TMBAB123456789012",
            is_default=True,
        )

        assert vehicle.customer == customer
        assert vehicle.vehicle_variant == variant
        assert vehicle.nickname == "My Octavia"
        assert vehicle.is_default is True

    def test_customer_can_have_multiple_vehicles(self):
        customer = self.create_customer("+201000000002")

        variant_1 = self.setup_vehicle_variant()

        make = VehicleMake.objects.get(name="Skoda")
        model = VehicleModel.objects.get(
            make=make,
            name="Octavia",
        )
        generation = VehicleGeneration.objects.get(
            model=model,
            name="A5",
        )

        engine_2 = VehicleEngine.objects.create(
            generation=generation,
            name="2.0 FSI",
            code="BLX",
            displacement_cc=1984,
            fuel_type="PETROL",
            power_hp=150,
        )

        variant_2 = VehicleVariant.objects.create(
            engine=engine_2,
            name="2.0 FSI Automatic",
            slug="2-0-fsi-automatic",
            transmission="AUTOMATIC",
            market="EGYPT",
        )

        vehicle_1 = CustomerVehicle.objects.create(
            customer=customer,
            vehicle_variant=variant_1,
            nickname="Daily",
            is_default=True,
        )

        vehicle_2 = CustomerVehicle.objects.create(
            customer=customer,
            vehicle_variant=variant_2,
            nickname="Second Car",
            is_default=False,
        )

        assert customer.vehicles.count() == 2
        assert vehicle_1.is_default is True
        assert vehicle_2.is_default is False

    def test_customer_cannot_have_two_default_vehicles(self):
        customer = self.create_customer("+201000000003")
        variant = self.setup_vehicle_variant()

        CustomerVehicle.objects.create(
            customer=customer,
            vehicle_variant=variant,
            nickname="First",
            is_default=True,
        )

        with pytest.raises(IntegrityError):
            CustomerVehicle.objects.create(
                customer=customer,
                vehicle_variant=variant,
                nickname="Second",
                is_default=True,
            )

    def test_different_customers_can_have_default_vehicles(self):
        customer_1 = self.create_customer("+201000000004")
        customer_2 = self.create_customer("+201000000005")
        variant = self.setup_vehicle_variant()

        vehicle_1 = CustomerVehicle.objects.create(
            customer=customer_1,
            vehicle_variant=variant,
            is_default=True,
        )

        vehicle_2 = CustomerVehicle.objects.create(
            customer=customer_2,
            vehicle_variant=variant,
            is_default=True,
        )

        assert vehicle_1.is_default is True
        assert vehicle_2.is_default is True

    def test_vehicle_variant_deletion_is_protected(self):
        customer = self.create_customer("+201000000006")
        variant = self.setup_vehicle_variant()

        CustomerVehicle.objects.create(
            customer=customer,
            vehicle_variant=variant,
        )

        with pytest.raises(Exception):
            variant.delete()

    def test_vin_is_normalized_by_clean(self):
        customer = self.create_customer("+201000000007")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicle(
            customer=customer,
            vehicle_variant=variant,
            vin="tmbab123456789012",
        )

        vehicle.full_clean()

        assert vehicle.vin == "TMBAB123456789012"

    def test_invalid_vin_length_is_rejected(self):
        customer = self.create_customer("+201000000008")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicle(
            customer=customer,
            vehicle_variant=variant,
            vin="ABC123",
        )

        with pytest.raises(Exception):
            vehicle.full_clean()

    def test_customer_cascade_deletes_vehicles(self):
        customer = self.create_customer("+201000000009")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicle.objects.create(
            customer=customer,
            vehicle_variant=variant,
        )

        vehicle_id = vehicle.id

        customer.delete()

        assert not CustomerVehicle.objects.filter(id=vehicle_id).exists()

    def test_customer_cannot_add_same_vehicle_variant_twice(self):
        customer = self.create_customer("+201000000010")
        variant = self.setup_vehicle_variant()

        CustomerVehicle.objects.create(
            customer=customer,
            vehicle_variant=variant,
            nickname="My Octavia",
        )

        with pytest.raises(IntegrityError):
            CustomerVehicle.objects.create(
                customer=customer,
                vehicle_variant=variant,
                nickname="Duplicate Octavia",
            )