from decimal import Decimal
from django.db import models, transaction
from django.db import transaction
from django.utils import timezone

from apps.finance.models import Commission, CommissionRule
from apps.orders.constants import OrderStatus


class CommissionService:

    @classmethod
    @transaction.atomic
    def create_for_order(cls, *, order):
        if order.status != OrderStatus.DELIVERED:
            raise ValueError(
                "Commission can only be created for DELIVERED orders."
            )

        existing = (
            Commission.objects
            .select_for_update()
            .filter(order=order)
            .first()
        )

        if existing:
            raise ValueError(
                "Commission already exists for this order."
            )

        now = timezone.now()

        rule = (
            CommissionRule.objects
            .select_for_update()
            .filter(
                store_id=order.store_id,
                is_active=True,
                effective_from__lte=now,
            )
            .filter(
                models.Q(effective_to__isnull=True)
                | models.Q(effective_to__gt=now)
            )
            .order_by("-effective_from")
            .first()
        )

        if rule is None:
            raise ValueError(
                "No active commission rule found for this store."
            )

        base_amount = (
            order.subtotal
            - order.seller_discount
        )

        if base_amount < Decimal("0.00"):
            raise ValueError(
                "Commission base amount cannot be negative."
            )

        commission_amount = (
            base_amount * rule.rate / Decimal("100")
        ).quantize(Decimal("0.01"))

        return Commission.objects.create(
            order=order,
            store=order.store,
            rate=rule.rate,
            base_amount=base_amount,
            commission_amount=commission_amount,
        )