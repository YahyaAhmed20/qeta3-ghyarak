import pytest

from apps.catalog.models import Category
from apps.catalog.services.category import CategoryService


@pytest.mark.django_db
class TestCategoryService:

    def test_create_root_category(self):
        category = CategoryService.create_category(
            name="Engine Parts",
            slug="engine-parts",
        )

        assert category.pk is not None
        assert category.name == "Engine Parts"
        assert category.slug == "engine-parts"
        assert category.parent is None
        assert category.is_active is True

    def test_create_child_category(self):
        parent = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        category = CategoryService.create_category(
            name="Filters",
            slug="filters",
            parent=parent,
        )

        assert category.parent == parent

    def test_cannot_create_under_inactive_parent(self):
        parent = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
            is_active=False,
        )

        with pytest.raises(ValueError, match="Parent category is not active."):
            CategoryService.create_category(
                name="Filters",
                slug="filters",
                parent=parent,
            )

    def test_change_parent(self):
        root = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        filters = Category.objects.create(
            name="Filters",
            slug="filters",
            parent=root,
        )

        oil_filters = Category.objects.create(
            name="Oil Filters",
            slug="oil-filters",
            parent=filters,
        )

        new_root = Category.objects.create(
            name="Body Parts",
            slug="body-parts",
        )

        updated = CategoryService.change_parent(
            category_id=oil_filters.id,
            parent=new_root,
        )

        updated.refresh_from_db()

        assert updated.parent == new_root

    def test_cannot_create_hierarchy_cycle(self):
        root = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        filters = Category.objects.create(
            name="Filters",
            slug="filters",
            parent=root,
        )

        oil_filters = Category.objects.create(
            name="Oil Filters",
            slug="oil-filters",
            parent=filters,
        )

        with pytest.raises(ValueError, match="Category hierarchy cycle detected."):
            CategoryService.change_parent(
                category_id=root.id,
                parent=oil_filters,
            )

    def test_cannot_change_parent_to_inactive_category(self):
        category = Category.objects.create(
            name="Filters",
            slug="filters",
        )

        inactive_parent = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
            is_active=False,
        )

        with pytest.raises(ValueError, match="Parent category is not active."):
            CategoryService.change_parent(
                category_id=category.id,
                parent=inactive_parent,
            )

    def test_change_parent_category_not_found(self):
        with pytest.raises(ValueError, match="Category not found."):
            CategoryService.change_parent(
                category_id="00000000-0000-0000-0000-000000000000",
                parent=None,
            )

    def test_deactivate_category(self):
        category = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
        )

        updated = CategoryService.deactivate_category(
            category_id=category.id,
        )

        updated.refresh_from_db()

        assert updated.is_active is False

    def test_activate_category(self):
        category = Category.objects.create(
            name="Engine Parts",
            slug="engine-parts",
            is_active=False,
        )

        updated = CategoryService.activate_category(
            category_id=category.id,
        )

        updated.refresh_from_db()

        assert updated.is_active is True

    def test_cannot_deactivate_category_not_found(self):
        with pytest.raises(ValueError, match="Category not found."):
            CategoryService.deactivate_category(
                category_id="00000000-0000-0000-0000-000000000000",
            )

    def test_cannot_activate_category_not_found(self):
        with pytest.raises(ValueError, match="Category not found."):
            CategoryService.activate_category(
                category_id="00000000-0000-0000-0000-000000000000",
            )