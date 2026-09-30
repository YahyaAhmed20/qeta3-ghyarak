from apps.addresses.models import Address


class AddressSelector:

    @staticmethod
    def get_address(*, address_id):
        return (
            Address.objects
            .select_related("customer")
            .filter(id=address_id)
            .first()
        )

    @staticmethod
    def get_customer_addresses(*, customer_id):
        return (
            Address.objects
            .filter(customer_id=customer_id)
            .order_by("-is_default", "-created_at")
        )

    @staticmethod
    def get_default_address(*, customer_id):
        return (
            Address.objects
            .filter(
                customer_id=customer_id,
                is_default=True,
            )
            .first()
        )