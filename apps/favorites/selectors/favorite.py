from apps.favorites.models import Favorite


class FavoriteSelector:

    @staticmethod
    def get_customer_favorites(*, customer):
        return (
            Favorite.objects
            .filter(customer=customer)
            .select_related("product", "product__category")
        )

    @staticmethod
    def get_favorite(*, customer, product):
        return (
            Favorite.objects
            .filter(
                customer=customer,
                product=product,
            )
            .select_related("product")
            .first()
        )

    @staticmethod
    def is_favorite(*, customer, product):
        return Favorite.objects.filter(
            customer=customer,
            product=product,
        ).exists()