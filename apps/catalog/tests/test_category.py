import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import Category


@pytest.mark.django_db
class TestCategory:

    def test_create_root_category(self):
        category = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        assert category.parent is None
        assert category.name == "Engine Parts"
        assert category.slug == "engine-parts"
        assert category.is_active is True

    def test_create_child_category(self):
        parent = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        child = Category.objects.create(
            parent=parent,
            name="Oil Filters",
            slug="oil-filters",
        )

        assert child.parent == parent
        assert child in parent.children.all()

    def test_category_name_must_be_unique_per_parent(self):
        parent = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        Category.objects.create(
            parent=parent,
            name="Filters",
            slug="filters",
        )

        with pytest.raises(Exception):
            Category.objects.create(
                parent=parent,
                name="Filters",
                slug="another-filters",
            )

    def test_same_name_allowed_under_different_parents(self):
        parent_1 = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        parent_2 = Category.objects.create(
            name="Brakes",
            slug="brakes",
        )

        category_1 = Category.objects.create(
            parent=parent_1,
            name="Filters",
            slug="filters",
        )

        category_2 = Category.objects.create(
            parent=parent_2,
            name="Filters",
            slug="filters",
        )

        assert category_1.id != category_2.id

    def test_category_slug_must_be_unique_per_parent(self):
        parent = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        Category.objects.create(
            parent=parent,
            name="Oil Filters",
            slug="oil-filters",
        )

        with pytest.raises(Exception):
            Category.objects.create(
                parent=parent,
                name="Different Name",
                slug="oil-filters",
            )

    def test_category_cannot_be_its_own_parent(self):
        category = Category(
            name="Engine Parts",
            slug="engine-parts",
        )

        category.parent = category

        with pytest.raises(ValidationError):
            category.full_clean()

    def test_root_categories_can_share_same_name(self):
        Category.objects.create(
            name="Filters",
            slug="filters",
        )

        Category.objects.create(
            name="Filters",
            slug="filters-2",
        )

        assert Category.objects.filter(
            parent__isnull=True,
            name="Filters",
        ).count() == 2