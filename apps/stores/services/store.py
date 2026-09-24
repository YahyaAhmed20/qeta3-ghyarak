from django.db import transaction

from apps.stores.models import Store, StoreStatus


class StoreService:
    @staticmethod
    @transaction.atomic
    def create_store(
        *,
        owner,
        name,
        slug,
        phone,
        address,
        city,
        description="",
        latitude=None,
        longitude=None,
    ):
        if owner.role not in {
            "SELLER_OWNER",
            "ADMIN",
            "SUPER_ADMIN",
        }:
            raise ValueError(
                "Only seller owners or administrators can create a store."
            )

        store = Store(
            owner=owner,
            name=name,
            slug=slug,
            phone=phone,
            address=address,
            city=city,
            description=description,
            latitude=latitude,
            longitude=longitude,
        )

        store.full_clean()
        store.save()

        return store

    @staticmethod
    @transaction.atomic
    def approve_store(*, store_id):
        store = (
            Store.objects
            .select_for_update()
            .filter(id=store_id)
            .first()
        )

        if store is None:
            raise ValueError("Store not found.")

        if store.status != StoreStatus.PENDING:
            raise ValueError(
                "Only pending stores can be approved."
            )

        store.status = StoreStatus.ACTIVE
        store.is_verified = True

        store.save(
            update_fields=[
                "status",
                "is_verified",
                "updated_at",
            ]
        )

        return store

    @staticmethod
    @transaction.atomic
    def update_store(
        *,
        store_id,
        owner,
        name=None,
        slug=None,
        description=None,
        phone=None,
        address=None,
        city=None,
        latitude=None,
        longitude=None,
    ):
        store = (
            Store.objects
            .select_for_update()
            .filter(
                id=store_id,
                owner=owner,
            )
            .first()
        )

        if store is None:
            raise ValueError("Store not found.")

        if store.status == StoreStatus.SUSPENDED:
            raise ValueError("Suspended stores cannot be updated.")

        if name is not None:
            store.name = name

        if slug is not None:
            store.slug = slug

        if description is not None:
            store.description = description

        if phone is not None:
            store.phone = phone

        if address is not None:
            store.address = address

        if city is not None:
            store.city = city

        if latitude is not None:
            store.latitude = latitude

        if longitude is not None:
            store.longitude = longitude

        store.full_clean()
        store.save()

        return store