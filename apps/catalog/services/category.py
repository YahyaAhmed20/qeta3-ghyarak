from django.db import transaction

from apps.catalog.models import Category


class CategoryService:

    @staticmethod
    @transaction.atomic
    def create_category(
        *,
        name,
        slug,
        parent=None,
        description="",
        is_active=True,
    ):
        if parent is not None and not parent.is_active:
            raise ValueError("Parent category is not active.")

        category = Category(
            name=name,
            slug=slug,
            parent=parent,
            description=description,
            is_active=is_active,
        )

        category.full_clean()
        category.save()

        return category

    @staticmethod
    @transaction.atomic
    def change_parent(*, category_id, parent=None):
        category = (
            Category.objects
            .select_for_update()
            .filter(id=category_id)
            .first()
        )

        if category is None:
            raise ValueError("Category not found.")

        if parent is not None:
            if not parent.is_active:
                raise ValueError("Parent category is not active.")

            if parent.id == category.id:
                raise ValueError(
                    "A category cannot be its own parent."
                )

            current_parent = parent

            while current_parent is not None:
                if current_parent.id == category.id:
                    raise ValueError(
                        "Category hierarchy cycle detected."
                    )

                current_parent = current_parent.parent

        category.parent = parent
        category.full_clean()
        category.save(
            update_fields=["parent", "updated_at"]
        )

        return category

    @staticmethod
    @transaction.atomic
    def deactivate_category(*, category_id):
        category = (
            Category.objects
            .select_for_update()
            .filter(id=category_id)
            .first()
        )

        if category is None:
            raise ValueError("Category not found.")

        category.is_active = False
        category.save(update_fields=["is_active", "updated_at"])

        return category

    @staticmethod
    @transaction.atomic
    def activate_category(*, category_id):
        category = (
            Category.objects
            .select_for_update()
            .filter(id=category_id)
            .first()
        )

        if category is None:
            raise ValueError("Category not found.")

        category.is_active = True
        category.save(update_fields=["is_active", "updated_at"])

        return category