import pytest

from apps.catalog.models import Brand
from apps.catalog.services.brand import BrandService


@pytest.mark.django_db
class TestBrandService:

    def test_create_brand(self):
        brand = BrandService.create_brand(
            name="Bosch",
            slug="bosch",
        )

        assert brand.pk is not None
        assert brand.name == "Bosch"
        assert brand.slug == "bosch"
        assert brand.is_active is True

    def test_create_brand_with_description(self):
        brand = BrandService.create_brand(
            name="Bosch",
            slug="bosch",
            description="German automotive parts brand.",
        )

        assert brand.description == "German automotive parts brand."

    def test_update_brand(self):
        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        updated = BrandService.update_brand(
            brand_id=brand.id,
            name="Bosch Automotive",
            slug="bosch-automotive",
            description="Updated description.",
        )

        updated.refresh_from_db()

        assert updated.name == "Bosch Automotive"
        assert updated.slug == "bosch-automotive"
        assert updated.description == "Updated description."

    def test_update_brand_partial(self):
        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
            description="Original description.",
        )

        updated = BrandService.update_brand(
            brand_id=brand.id,
            name="Bosch Automotive",
        )

        updated.refresh_from_db()

        assert updated.name == "Bosch Automotive"
        assert updated.slug == "bosch"
        assert updated.description == "Original description."

    def test_update_brand_not_found(self):
        with pytest.raises(ValueError, match="Brand not found."):
            BrandService.update_brand(
                brand_id="00000000-0000-0000-0000-000000000000",
                name="Bosch",
            )

    def test_deactivate_brand(self):
        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        updated = BrandService.deactivate_brand(
            brand_id=brand.id,
        )

        updated.refresh_from_db()

        assert updated.is_active is False

    def test_activate_brand(self):
        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
            is_active=False,
        )

        updated = BrandService.activate_brand(
            brand_id=brand.id,
        )

        updated.refresh_from_db()

        assert updated.is_active is True

    def test_deactivate_brand_not_found(self):
        with pytest.raises(ValueError, match="Brand not found."):
            BrandService.deactivate_brand(
                brand_id="00000000-0000-0000-0000-000000000000",
            )

    def test_activate_brand_not_found(self):
        with pytest.raises(ValueError, match="Brand not found."):
            BrandService.activate_brand(
                brand_id="00000000-0000-0000-0000-000000000000",
            )