from django.db.models import Q, Prefetch

from apps.catalog.models import Product
from apps.catalog.models.compatibility import CompatibilityStatus
from apps.inventory.models import Inventory
from apps.stores.models import SellerProduct


class MarketplaceProductSelector:

    @staticmethod
    def get_products(
    *,
    search=None,
    category_id=None,
    brand_id=None,
    vehicle_id=None,
):
        queryset = (
            Product.objects
            .filter(
                is_active=True,
                seller_products__is_active=True,
                seller_products__store__status="ACTIVE",
                seller_products__store__is_verified=True,
            )
        )

        if search:
            normalized_search = "".join(
                character
                for character in search.upper().strip()
                if character.isalnum()
            )

            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(
                    part_numbers__normalized_part_number__icontains=
                    normalized_search
                )
            )
        if category_id:
            queryset = queryset.filter(
                category_id=category_id,
            )
            
        if brand_id:
            queryset = queryset.filter(
                brand_id=brand_id,
            )
            
        if vehicle_id:
            queryset = queryset.filter(
                compatibilities__vehicle_variant_id=vehicle_id,
                compatibilities__status=CompatibilityStatus.APPROVED,
            )

        return (
            queryset
            .select_related(
                "category",
                "brand",
            )
            .prefetch_related(
                "part_numbers",
                "compatibilities",
                Prefetch(
                    "seller_products",
                    queryset=(
                        SellerProduct.objects
                        .filter(
                            is_active=True,
                            store__status="ACTIVE",
                            store__is_verified=True,
                            inventory__isnull=False,
                        )
                        .select_related(
                            "store",
                            "inventory",
                        )
                    ),
                ),
            )
            .distinct()
            .order_by("name")
        )