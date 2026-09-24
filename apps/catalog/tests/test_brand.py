import pytest

from apps.catalog.models import Brand


@pytest.mark.django_db
class TestBrand:

    def test_create_brand(self):
        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        assert brand.pk is not None
        assert brand.name == "Bosch"
        assert brand.slug == "bosch"
        assert brand.is_active is True

    def test_brand_name_must_be_unique(self):
        Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        with pytest.raises(Exception):
            Brand.objects.create(
                name="Bosch",
                slug="bosch-2",
            )

    def test_brand_slug_must_be_unique(self):
        Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        with pytest.raises(Exception):
            Brand.objects.create(
                name="Bosch Motors",
                slug="bosch",
            )

    def test_brand_can_be_inactive(self):
        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
            is_active=False,
        )

        assert brand.is_active is False

    def test_brand_description_is_optional(self):
        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        assert brand.description == ""

    def test_brand_string_representation(self):
        brand = Brand.objects.create(
            name="Bosch",
            slug="bosch",
        )

        assert str(brand) == "Bosch"