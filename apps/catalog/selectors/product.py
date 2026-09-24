from apps.catalog.models import Product


class ProductSelector:

    @staticmethod
    def get_active_products():
        return (
            Product.objects
            .filter(is_active=True)
            .select_related("category", "brand")
        )

    @staticmethod
    def get_active_product(*, product_id):
        return (
            Product.objects
            .filter(
                id=product_id,
                is_active=True,
            )
            .select_related("category", "brand")
            .first()
        )