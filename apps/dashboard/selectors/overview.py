from decimal import Decimal

from django.db import models
from django.db.models import (
    DecimalField,
    F,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.finance.models.settlement import Settlement, SettlementStatus
from apps.inventory.models.inventory import Inventory
from apps.orders.models.order import Order, OrderStatus
from apps.stores.models.seller_product import SellerProduct


class DashboardOverviewSelector:
    """
    Read-only queries for the seller dashboard overview.
    """

    @staticmethod
    def get_overview(store):
        today = timezone.localdate()

        orders = Order.objects.filter(store=store)

        today_orders = orders.filter(
            created_at__date=today
        )

        pending_orders = orders.filter(
            status__in=[
                OrderStatus.CREATED,
                OrderStatus.ACCEPTED,
                OrderStatus.PREPARING,
                OrderStatus.READY,
                OrderStatus.OUT_FOR_DELIVERY,
            ]
        )

        delivered_orders = orders.filter(
            status=OrderStatus.DELIVERED
        )

        sales_expression = models.ExpressionWrapper(
            F("subtotal") - F("seller_discount"),
            output_field=DecimalField(
                max_digits=14,
                decimal_places=2,
            ),
        )

        money_zero = Value(
            Decimal("0.00"),
            output_field=DecimalField(
                max_digits=14,
                decimal_places=2,
            ),
        )

        today_sales = today_orders.filter(
            status=OrderStatus.DELIVERED
        ).aggregate(
            total=Coalesce(
                Sum(sales_expression),
                money_zero,
            )
        )["total"]

        total_sales = delivered_orders.aggregate(
            total=Coalesce(
                Sum(sales_expression),
                money_zero,
            )
        )["total"]

        seller_products = SellerProduct.objects.filter(
            store=store,
            is_active=True,
        )

        inventory = Inventory.objects.filter(
            seller_product__store=store,
            seller_product__is_active=True,
        )

        settlements = Settlement.objects.filter(
            store=store,
        )

        settlement_totals = settlements.aggregate(
            pending=Coalesce(
                Sum(
                    "net_amount",
                    filter=Q(
                        status=SettlementStatus.PENDING
                    ),
                ),
                money_zero,
            ),
            ready=Coalesce(
                Sum(
                    "net_amount",
                    filter=Q(
                        status=SettlementStatus.READY
                    ),
                ),
                money_zero,
            ),
            processing=Coalesce(
                Sum(
                    "net_amount",
                    filter=Q(
                        status=SettlementStatus.PROCESSING
                    ),
                ),
                money_zero,
            ),
            paid=Coalesce(
                Sum(
                    "net_amount",
                    filter=Q(
                        status=SettlementStatus.PAID
                    ),
                ),
                money_zero,
            ),
        )

        return {
            "store": {
                "id": store.id,
                "name": store.name,
                "status": store.status,
                "is_verified": store.is_verified,
            },
            "orders": {
                "total": orders.count(),
                "today": today_orders.count(),
                "pending": pending_orders.count(),
                "delivered": delivered_orders.count(),
            },
            "sales": {
                "today": today_sales,
                "total": total_sales,
            },
            "inventory": {
                "total_products": seller_products.count(),
                "out_of_stock": inventory.filter(
                    on_hand=F("reserved")
                ).count(),
            },
            "settlements": settlement_totals,
        }