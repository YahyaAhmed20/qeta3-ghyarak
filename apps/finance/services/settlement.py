# apps/finance/services/settlement.py

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.finance.models import Commission, Settlement
from apps.finance.models.settlement_item import SettlementItem
from apps.stores.models import Store, StoreStatus


class SettlementService:

    @staticmethod
    @transaction.atomic
    def create_settlement(
        *,
        store_id,
        period_start,
        period_end,
    ):
        store = (
            Store.objects
            .select_for_update()
            .get(id=store_id)
        )

        if store.status != StoreStatus.ACTIVE:
            raise ValueError("Store must be active.")

        if not store.is_verified:
            raise ValueError("Store must be verified.")

        if period_start >= period_end:
            raise ValueError(
                "Settlement period start must be before period end."
            )

        overlapping = (
            Settlement.objects
            .select_for_update()
            .filter(
                store_id=store_id,
                period_start__lt=period_end,
                period_end__gt=period_start,
            )
            .exists()
        )

        if overlapping:
            raise ValueError(
                "Settlement period overlaps an existing settlement."
            )

        return Settlement.objects.create(
            store=store,
            period_start=period_start,
            period_end=period_end,
            gross_sales=0,
            commission_total=0,
            adjustments_total=0,
            net_amount=0,
        )

    @staticmethod
    def _calculate_adjustments_total(settlement):
        total = Decimal("0.00")

        for adjustment in settlement.adjustments.all():
            total += adjustment.signed_amount

        return total

    @staticmethod
    @transaction.atomic
    def add_commissions(*, settlement_id):
        settlement = (
            Settlement.objects
            .select_for_update()
            .get(id=settlement_id)
        )

        commissions = (
            Commission.objects
            .select_for_update()
            .filter(
                store_id=settlement.store_id,
                status__in=["PENDING", "READY"],
                created_at__date__gte=settlement.period_start,
                created_at__date__lt=settlement.period_end,
                settlement_item__isnull=True,
            )
        )

        for commission in commissions:
            SettlementItem.objects.create(
                settlement=settlement,
                commission=commission,
                gross_amount=commission.base_amount,
                commission_amount=commission.commission_amount,
            )

        totals = settlement.items.aggregate(
            gross_sales=Sum("gross_amount"),
            commission_total=Sum("commission_amount"),
        )

        adjustments_total = (
            SettlementService._calculate_adjustments_total(settlement)
        )

        settlement.gross_sales = (
            totals["gross_sales"] or Decimal("0.00")
        )
        settlement.commission_total = (
            totals["commission_total"] or Decimal("0.00")
        )
        settlement.adjustments_total = adjustments_total

        settlement.net_amount = (
            settlement.gross_sales
            - settlement.commission_total
            + settlement.adjustments_total
        )

        settlement.save(
            update_fields=[
                "gross_sales",
                "commission_total",
                "adjustments_total",
                "net_amount",
                "updated_at",
            ]
        )

        return settlement

    @staticmethod
    @transaction.atomic
    def mark_ready(*, settlement_id):
        settlement = (
            Settlement.objects
            .select_for_update()
            .get(id=settlement_id)
        )

        if settlement.status != "PENDING":
            raise ValueError(
                "Settlement must be pending."
            )

        if not settlement.items.exists():
            raise ValueError(
                "Settlement must contain at least one item."
            )

        settlement.status = "READY"

        settlement.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return settlement

    @staticmethod
    @transaction.atomic
    def start_processing(*, settlement_id):
        settlement = (
            Settlement.objects
            .select_for_update()
            .get(id=settlement_id)
        )

        if settlement.status != "READY":
            raise ValueError(
                "Settlement must be ready."
            )

        settlement.status = "PROCESSING"

        settlement.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return settlement

    @staticmethod
    @transaction.atomic
    def mark_paid(
        *,
        settlement_id,
        payment_reference,
    ):
        settlement = (
            Settlement.objects
            .select_for_update()
            .get(id=settlement_id)
        )

        if settlement.status != "PROCESSING":
            raise ValueError(
                "Settlement must be processing."
            )

        if not payment_reference or not payment_reference.strip():
            raise ValueError(
                "Payment reference is required."
            )

        settlement.status = "PAID"
        settlement.payment_reference = payment_reference.strip()
        settlement.paid_at = timezone.now()

        settlement.save(
            update_fields=[
                "status",
                "payment_reference",
                "paid_at",
                "updated_at",
            ]
        )

        for item in settlement.items.select_related("commission"):
            commission = item.commission

            commission.status = "SETTLED"
            commission.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        return settlement

    @staticmethod
    @transaction.atomic
    def dispute(*, settlement_id):
        settlement = (
            Settlement.objects
            .select_for_update()
            .get(id=settlement_id)
        )

        if settlement.status == "PAID":
            raise ValueError(
                "Paid settlement cannot be disputed."
            )

        if settlement.status == "CANCELLED":
            raise ValueError(
                "Cancelled settlement cannot be disputed."
            )

        if settlement.status not in {
            "PENDING",
            "READY",
            "PROCESSING",
        }:
            raise ValueError(
                "Settlement cannot be disputed."
            )

        settlement.status = "DISPUTED"

        settlement.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return settlement

    @staticmethod
    @transaction.atomic
    def cancel(*, settlement_id):
        settlement = (
            Settlement.objects
            .select_for_update()
            .get(id=settlement_id)
        )

        if settlement.status == "PROCESSING":
            raise ValueError(
                "Processing settlement cannot be cancelled."
            )

        if settlement.status == "PAID":
            raise ValueError(
                "Paid settlement cannot be cancelled."
            )

        if settlement.status == "DISPUTED":
            raise ValueError(
                "Disputed settlement cannot be cancelled."
            )

        if settlement.status not in {
            "PENDING",
            "READY",
        }:
            raise ValueError(
                "Settlement cannot be cancelled."
            )

        settlement.status = "CANCELLED"

        settlement.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return settlement