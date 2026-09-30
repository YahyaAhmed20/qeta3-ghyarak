from apps.reviews.models import Review


class ReviewSelector:

    @staticmethod
    def get_review(*, review_id):
        return (
            Review.objects
            .select_related(
                "customer",
                "store",
                "product",
                "order",
            )
            .filter(id=review_id)
            .first()
        )

    @staticmethod
    def get_customer_reviews(*, customer_id):
        return (
            Review.objects
            .select_related(
                "customer",
                "store",
                "product",
                "order",
            )
            .filter(customer_id=customer_id)
            .order_by("-created_at")
        )

    @staticmethod
    def get_store_reviews(*, store_id):
        return (
            Review.objects
            .select_related(
                "customer",
                "store",
                "product",
                "order",
            )
            .filter(
                store_id=store_id,
            )
            .order_by("-created_at")
        )

    @staticmethod
    def get_product_reviews(*, product_id):
        return (
            Review.objects
            .select_related(
                "customer",
                "store",
                "product",
                "order",
            )
            .filter(
                product_id=product_id,
            )
            .order_by("-created_at")
        )

    @staticmethod
    def get_order_reviews(*, order_id):
        return (
            Review.objects
            .select_related(
                "customer",
                "store",
                "product",
                "order",
            )
            .filter(
                order_id=order_id,
            )
            .order_by("-created_at")
        )