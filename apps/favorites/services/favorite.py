from django.db import transaction

from apps.favorites.models import Favorite


class FavoriteService:

    @staticmethod
    @transaction.atomic
    def add_favorite(*, customer, product):
        favorite, _ = Favorite.objects.get_or_create(
            customer=customer,
            product=product,
        )
        return favorite

    @staticmethod
    @transaction.atomic
    def remove_favorite(*, customer, product):
        deleted, _ = Favorite.objects.filter(
            customer=customer,
            product=product,
        ).delete()

        return deleted > 0