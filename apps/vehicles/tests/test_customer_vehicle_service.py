import pytest

from apps.accounts.models import User
from apps.vehicles.models import (
    CustomerVehicle,
    VehicleEngine,
    VehicleGeneration,
    VehicleMake,
    VehicleModel,
    VehicleVariant,
)
from apps.vehicles.services.customer_vehicle import CustomerVehicleService


@pytest.mark.django_db
class TestCustomerVehicleService:

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

        return VehicleVariant.objects.create(
            engine=engine,
            name="1.6 MPI Manual",
            slug="1-6-mpi-manual",
            transmission="MANUAL",
            market="EGYPT",
        )

    def create_customer(self, phone):
        return User.objects.create_user(
            phone=phone,
            password="TestPassword123!",
            role="CUSTOMER",
        )

    def test_add_first_vehicle_makes_it_default(self):
        customer = self.create_customer("+201000000011")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
            nickname="My Octavia",
        )

        assert vehicle.customer == customer
        assert vehicle.vehicle_variant == variant
        assert vehicle.is_default is True

    def test_add_second_vehicle_does_not_make_it_default(self):
        customer = self.create_customer("+201000000012")
        variant_1 = self.setup_vehicle_variant()

        vehicle_1 = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant_1,
            nickname="First Car",
        )

        engine_2 = VehicleEngine.objects.create(
            generation=variant_1.engine.generation,
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
        )

        vehicle_2 = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant_2,
            nickname="Second Car",
        )

        assert vehicle_1.is_default is True
        assert vehicle_2.is_default is False

    def test_add_vehicle_rejects_inactive_variant(self):
        customer = self.create_customer("+201000000013")
        variant = self.setup_vehicle_variant()

        variant.is_active = False
        variant.save(update_fields=["is_active"])

        with pytest.raises(ValueError, match="not active"):
            CustomerVehicleService.add_vehicle(
                customer=customer,
                vehicle_variant=variant,
            )

        assert CustomerVehicle.objects.count() == 0

    def test_add_vehicle_rejects_duplicate_variant(self):
        customer = self.create_customer("+201000000014")
        variant = self.setup_vehicle_variant()

        CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
        )

        with pytest.raises(
            ValueError,
            match="already has this vehicle",
        ):
            CustomerVehicleService.add_vehicle(
                customer=customer,
                vehicle_variant=variant,
            )

        assert CustomerVehicle.objects.count() == 1

    def test_set_default_changes_default_vehicle(self):
        customer = self.create_customer("+201000000015")
        variant_1 = self.setup_vehicle_variant()

        vehicle_1 = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant_1,
            nickname="First Car",
        )

        engine_2 = VehicleEngine.objects.create(
            generation=variant_1.engine.generation,
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
        )

        vehicle_2 = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant_2,
            nickname="Second Car",
        )

        result = CustomerVehicleService.set_default(
            customer=customer,
            vehicle_id=vehicle_2.id,
        )

        vehicle_1.refresh_from_db()
        vehicle_2.refresh_from_db()

        assert result.id == vehicle_2.id
        assert vehicle_1.is_default is False
        assert vehicle_2.is_default is True

    def test_set_default_returns_same_vehicle_if_already_default(self):
        customer = self.create_customer("+201000000016")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
        )

        result = CustomerVehicleService.set_default(
            customer=customer,
            vehicle_id=vehicle.id,
        )

        vehicle.refresh_from_db()

        assert result.id == vehicle.id
        assert vehicle.is_default is True

    def test_set_default_rejects_vehicle_owned_by_another_customer(self):
        customer_1 = self.create_customer("+201000000017")
        customer_2 = self.create_customer("+201000000018")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer_1,
            vehicle_variant=variant,
        )

        with pytest.raises(
            ValueError,
            match="Customer vehicle not found",
        ):
            CustomerVehicleService.set_default(
                customer=customer_2,
                vehicle_id=vehicle.id,
            )

        vehicle.refresh_from_db()

        assert vehicle.customer == customer_1
        assert vehicle.is_default is True

    def test_set_default_rejects_unknown_vehicle(self):
        customer = self.create_customer("+201000000019")

        with pytest.raises(
            ValueError,
            match="Customer vehicle not found",
        ):
            CustomerVehicleService.set_default(
                customer=customer,
                vehicle_id="00000000-0000-0000-0000-000000000000",
            )

    def test_remove_non_default_vehicle(self):
        customer = self.create_customer("+201000000020")
        variant_1 = self.setup_vehicle_variant()

        vehicle_1 = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant_1,
            nickname="First Car",
        )

        engine_2 = VehicleEngine.objects.create(
            generation=variant_1.engine.generation,
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
        )

        vehicle_2 = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant_2,
            nickname="Second Car",
        )

        CustomerVehicleService.remove_vehicle(
            customer=customer,
            vehicle_id=vehicle_2.id,
        )

        assert not CustomerVehicle.objects.filter(
            id=vehicle_2.id
        ).exists()

        vehicle_1.refresh_from_db()
        assert vehicle_1.is_default is True

    def test_remove_default_vehicle_promotes_another_vehicle(self):
        customer = self.create_customer("+201000000021")
        variant_1 = self.setup_vehicle_variant()

        vehicle_1 = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant_1,
            nickname="First Car",
        )

        engine_2 = VehicleEngine.objects.create(
            generation=variant_1.engine.generation,
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
        )

        vehicle_2 = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant_2,
            nickname="Second Car",
        )

        CustomerVehicleService.remove_vehicle(
            customer=customer,
            vehicle_id=vehicle_1.id,
        )

        assert not CustomerVehicle.objects.filter(
            id=vehicle_1.id
        ).exists()

        vehicle_2.refresh_from_db()
        assert vehicle_2.is_default is True

    def test_remove_last_vehicle_leaves_no_default(self):
        customer = self.create_customer("+201000000022")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
        )

        CustomerVehicleService.remove_vehicle(
            customer=customer,
            vehicle_id=vehicle.id,
        )

        assert CustomerVehicle.objects.filter(
            customer=customer
        ).count() == 0

    def test_remove_vehicle_rejects_vehicle_owned_by_another_customer(self):
        customer_1 = self.create_customer("+201000000023")
        customer_2 = self.create_customer("+201000000024")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer_1,
            vehicle_variant=variant,
        )

        with pytest.raises(
            ValueError,
            match="Customer vehicle not found",
        ):
            CustomerVehicleService.remove_vehicle(
                customer=customer_2,
                vehicle_id=vehicle.id,
            )

        assert CustomerVehicle.objects.filter(
            id=vehicle.id
        ).exists()

    def test_update_vehicle_updates_allowed_fields(self):
        customer = self.create_customer("+201000000025")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
            nickname="Old Name",
            plate_number="ABC 123",
            vin="TMBAB123456789012",
        )

        updated_vehicle = CustomerVehicleService.update_vehicle(
            customer=customer,
            vehicle_id=vehicle.id,
            nickname="New Name",
            plate_number="XYZ 789",
            vin="WVWZZZ12345678901",
        )

        updated_vehicle.refresh_from_db()

        assert updated_vehicle.nickname == "New Name"
        assert updated_vehicle.plate_number == "XYZ 789"
        assert updated_vehicle.vin == "WVWZZZ12345678901"
        assert updated_vehicle.vehicle_variant == variant
        assert updated_vehicle.is_default is True

    def test_update_vehicle_supports_partial_updates(self):
        customer = self.create_customer("+201000000026")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
            nickname="My Octavia",
            plate_number="ABC 123",
            vin="TMBAB123456789012",
        )

        updated_vehicle = CustomerVehicleService.update_vehicle(
            customer=customer,
            vehicle_id=vehicle.id,
            nickname="Updated Octavia",
        )

        updated_vehicle.refresh_from_db()

        assert updated_vehicle.nickname == "Updated Octavia"
        assert updated_vehicle.plate_number == "ABC 123"
        assert updated_vehicle.vin == "TMBAB123456789012"

    def test_update_vehicle_rejects_vehicle_owned_by_another_customer(self):
        customer_1 = self.create_customer("+201000000027")
        customer_2 = self.create_customer("+201000000028")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer_1,
            vehicle_variant=variant,
        )

        with pytest.raises(
            ValueError,
            match="Customer vehicle not found",
        ):
            CustomerVehicleService.update_vehicle(
                customer=customer_2,
                vehicle_id=vehicle.id,
                nickname="Hacked",
            )

        vehicle.refresh_from_db()

        assert vehicle.customer == customer_1
        assert vehicle.nickname == ""

    def test_update_vehicle_rejects_invalid_vin(self):
        customer = self.create_customer("+201000000029")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
            vin="TMBAB123456789012",
        )

        with pytest.raises(Exception):
            CustomerVehicleService.update_vehicle(
                customer=customer,
                vehicle_id=vehicle.id,
                vin="INVALID",
            )

        vehicle.refresh_from_db()

        assert vehicle.vin == "TMBAB123456789012"

    def test_update_vehicle_normalizes_vin(self):
        customer = self.create_customer("+201000000030")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
            vin="TMBAB123456789012",
        )

        updated_vehicle = CustomerVehicleService.update_vehicle(
            customer=customer,
            vehicle_id=vehicle.id,
            vin="1hg cm826 33a123456",
        )

        updated_vehicle.refresh_from_db()

        assert updated_vehicle.vin == "1HGCM82633A123456"

    def test_add_vehicle_normalizes_vin(self):
        customer = self.create_customer("+201000000031")
        variant = self.setup_vehicle_variant()

        vehicle = CustomerVehicleService.add_vehicle(
            customer=customer,
            vehicle_variant=variant,
            vin="1hg cm826 33a123456",
        )

        vehicle.refresh_from_db()

        assert vehicle.vin == "1HGCM82633A123456"

    def test_add_vehicle_rejects_invalid_vin(self):
        customer = self.create_customer("+201000000032")
        variant = self.setup_vehicle_variant()

        with pytest.raises(Exception):
            CustomerVehicleService.add_vehicle(
                customer=customer,
                vehicle_variant=variant,
                vin="INVALID",
            )

        assert CustomerVehicle.objects.count() == 0