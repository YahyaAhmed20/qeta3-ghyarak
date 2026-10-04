from django.db.models import (
    DecimalField,
    F,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
)
from django.db.models.functions import Coalesce

from apps.catalog.models import Product, ProductCompatibility
from apps.stores.models import SellerProduct


class MarketplaceProductSelector:

    @staticmethod
    def get_products(
        *,
        search=None,
        category_id=None,
        brand_id=None,
        vehicle_id=None,
        ordering=None,
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
                compatibilities__status="APPROVED",
            )

        seller_product_price = (
            SellerProduct.objects
            .filter(
                product_id=OuterRef("pk"),
                is_active=True,
                store__status="ACTIVE",
                store__is_verified=True,
                inventory__isnull=False,
                inventory__on_hand__gt=F("inventory__reserved"),
            )
            .annotate(
                effective_price=Coalesce(
                    "sale_price",
                    "price",
                )
            )
            .order_by("effective_price", "id")
            .values("effective_price")[:1]
        )

        queryset = queryset.annotate(
            min_price=Subquery(
                seller_product_price,
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2,
                ),
            )
        )

        allowed_orderings = {
            "price": "min_price",
            "-price": "-min_price",
            "name": "name",
            "-name": "-name",
        }
        order_by = allowed_orderings.get(ordering, "name")

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
                            inventory__on_hand__gt=F(
                                "inventory__reserved"
                            ),
                        )
                        .select_related(
                            "store",
                            "inventory",
                        )
                    ),
                ),
            )
            .distinct()
            .order_by(order_by, "id")
        )

    @staticmethod
    def get_product_detail(*, product_id):
        seller_product_price = (
            SellerProduct.objects
            .filter(
                product_id=OuterRef("pk"),
                is_active=True,
                store__status="ACTIVE",
                store__is_verified=True,
                inventory__isnull=False,
                inventory__on_hand__gt=F("inventory__reserved"),
            )
            .annotate(
                effective_price=Coalesce(
                    "sale_price",
                    "price",
                )
            )
            .order_by("effective_price", "id")
            .values("effective_price")[:1]
        )

        return (
            Product.objects
            .filter(
                id=product_id,
                is_active=True,
                seller_products__is_active=True,
                seller_products__store__status="ACTIVE",
                seller_products__store__is_verified=True,
                seller_products__inventory__isnull=False,
                seller_products__inventory__on_hand__gt=F(
                    "seller_products__inventory__reserved"
                ),
            )
            .annotate(
                min_price=Subquery(
                    seller_product_price,
                    output_field=DecimalField(
                        max_digits=12,
                        decimal_places=2,
                    ),
                )
            )
            .select_related(
                "category",
                "brand",
            )
            .prefetch_related(
                "part_numbers",
                Prefetch(
                    "compatibilities",
                    queryset=(
                        ProductCompatibility.objects
                        .filter(
                            status="APPROVED",
                        )
                        .select_related(
                            "vehicle_variant",
                            "vehicle_variant__engine",
                            "vehicle_variant__engine__generation",
                            "vehicle_variant__engine__generation__model",
                            "vehicle_variant__engine__generation__model__make",
                        )
                    ),
                ),
                Prefetch(
                    "seller_products",
                    queryset=(
                        SellerProduct.objects
                        .filter(
                            is_active=True,
                            store__status="ACTIVE",
                            store__is_verified=True,
                            inventory__isnull=False,
                            inventory__on_hand__gt=F(
                                "inventory__reserved"
                            ),
                        )
                        .select_related(
                            "store",
                            "inventory",
                        )
                        .order_by("id")
                    ),
                ),
            )
            .first()
        )