import pytest

from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.accounts.models import User
from apps.finance.models import (
    Commission,
    Settlement,
    SettlementItem,
    SettlementStatus,
)
from apps.finance.services.settlement import SettlementService
from apps.stores.models import Store, StoreStatus


@pytest.mark.django_db
class TestCreateSettlement:

    def test_create_settlement_success(self, active_store):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        assert settlement.store_id == active_store.id
        assert settlement.period_start == date(2026, 9, 1)
        assert settlement.period_end == date(2026, 9, 8)

        assert settlement.status == SettlementStatus.PENDING

        assert settlement.gross_sales == Decimal("0.00")
        assert settlement.commission_total == Decimal("0.00")
        assert settlement.adjustments_total == Decimal("0.00")
        assert settlement.net_amount == Decimal("0.00")

    def test_inactive_store_rejected(self, active_store):
        active_store.status = StoreStatus.SUSPENDED
        active_store.save(update_fields=["status"])

        with pytest.raises(ValueError, match="Store must be active"):
            SettlementService.create_settlement(
                store_id=active_store.id,
                period_start=date(2026, 9, 1),
                period_end=date(2026, 9, 8),
            )

    def test_unverified_store_rejected(self, active_store):
        active_store.is_verified = False
        active_store.save(update_fields=["is_verified"])

        with pytest.raises(ValueError, match="Store must be verified"):
            SettlementService.create_settlement(
                store_id=active_store.id,
                period_start=date(2026, 9, 1),
                period_end=date(2026, 9, 8),
            )

    @pytest.mark.parametrize(
        ("period_start", "period_end"),
        [
            (date(2026, 9, 8), date(2026, 9, 8)),
            (date(2026, 9, 10), date(2026, 9, 1)),
        ],
    )
    def test_invalid_period_rejected(
        self,
        active_store,
        period_start,
        period_end,
    ):
        with pytest.raises(
            ValueError,
            match="Settlement period start must be before period end",
        ):
            SettlementService.create_settlement(
                store_id=active_store.id,
                period_start=period_start,
                period_end=period_end,
            )

    def test_overlapping_period_rejected(self, active_store):
        SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        with pytest.raises(
            ValueError,
            match="Settlement period overlaps",
        ):
            SettlementService.create_settlement(
                store_id=active_store.id,
                period_start=date(2026, 9, 5),
                period_end=date(2026, 9, 12),
            )

    def test_contiguous_period_allowed(self, active_store):
        SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 8),
            period_end=date(2026, 9, 15),
        )

        assert settlement.period_start == date(2026, 9, 8)
        assert settlement.period_end == date(2026, 9, 15)

        assert Settlement.objects.filter(
            store=active_store
        ).count() == 2

    def test_same_period_rejected(self, active_store):
        SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        with pytest.raises(
            ValueError,
            match="Settlement period overlaps",
        ):
            SettlementService.create_settlement(
                store_id=active_store.id,
                period_start=date(2026, 9, 1),
                period_end=date(2026, 9, 8),
            )


@pytest.mark.django_db
class TestAddCommissions:

    def test_add_commissions_success(
        self,
        active_store,
        order,
        commission_rule,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        result = SettlementService.add_commissions(
            settlement_id=settlement.id,
        )

        result.refresh_from_db()

        assert SettlementItem.objects.filter(
            settlement=result,
            commission=commission,
        ).count() == 1

        assert result.gross_sales == Decimal("250.00")
        assert result.commission_total == Decimal("17.50")
        assert result.adjustments_total == Decimal("0.00")
        assert result.net_amount == Decimal("232.50")

    def test_commission_from_another_store_is_not_added(
        self,
        active_store,
        order,
    ):
        other_owner = User.objects.create_user(
            phone="+201001234568",
            role="SELLER_OWNER",
        )

        other_store = Store.objects.create(
            owner=other_owner,
            name="Other Store",
            slug="other-store",
            phone="+201001234568",
            address="Suez",
            city="Suez",
            status=StoreStatus.ACTIVE,
            is_verified=True,
        )

        order.store = other_store
        order.save(update_fields=["store"])

        commission = Commission.objects.create(
            order=order,
            store=other_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        result = SettlementService.add_commissions(
            settlement_id=settlement.id,
        )

        assert not SettlementItem.objects.filter(
            settlement=result,
            commission=commission,
        ).exists()

        assert result.gross_sales == Decimal("0.00")
        assert result.commission_total == Decimal("0.00")
        assert result.net_amount == Decimal("0.00")

    def test_commission_outside_period_is_not_added(
        self,
        active_store,
        order,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
            created_at=timezone.now() - timedelta(days=10),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=2)).date(),
            period_end=(timezone.now() - timedelta(days=1)).date(),
        )

        result = SettlementService.add_commissions(
            settlement_id=settlement.id,
        )

        assert not SettlementItem.objects.filter(
            settlement=result,
            commission=commission,
        ).exists()

    def test_existing_settlement_item_is_not_added_twice(
        self,
        active_store,
        order,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        SettlementItem.objects.create(
            settlement=settlement,
            commission=commission,
            gross_amount=commission.base_amount,
            commission_amount=commission.commission_amount,
        )

        result = SettlementService.add_commissions(
            settlement_id=settlement.id,
        )

        assert SettlementItem.objects.filter(
            commission=commission,
        ).count() == 1

        assert result.gross_sales == Decimal("250.00")
        assert result.commission_total == Decimal("17.50")
        assert result.net_amount == Decimal("232.50")

    def test_credit_adjustment_is_included_in_net_amount(
        self,
        active_store,
        order,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        SettlementItem.objects.create(
            settlement=settlement,
            commission=commission,
            gross_amount=commission.base_amount,
            commission_amount=commission.commission_amount,
        )

        from apps.finance.models import SettlementAdjustment
        from apps.accounts.models import User

        admin = User.objects.create_user(
            phone="+201001234569",
            role="ADMIN",
        )

        SettlementAdjustment.objects.create(
            settlement=settlement,
            adjustment_type="SELLER_CREDIT",
            amount=Decimal("20.00"),
            reason="Seller credit",
            created_by=admin,
        )

        result = SettlementService.add_commissions(
            settlement_id=settlement.id,
        )

        assert result.gross_sales == Decimal("250.00")
        assert result.commission_total == Decimal("17.50")
        assert result.adjustments_total == Decimal("20.00")
        assert result.net_amount == Decimal("252.50")

    def test_debit_adjustment_is_included_as_negative(
        self,
        active_store,
        order,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        SettlementItem.objects.create(
            settlement=settlement,
            commission=commission,
            gross_amount=commission.base_amount,
            commission_amount=commission.commission_amount,
        )

        from apps.finance.models import SettlementAdjustment
        from apps.accounts.models import User

        admin = User.objects.create_user(
            phone="+201001234570",
            role="ADMIN",
        )

        SettlementAdjustment.objects.create(
            settlement=settlement,
            adjustment_type="SELLER_DEBIT",
            amount=Decimal("10.00"),
            reason="Seller debit",
            created_by=admin,
        )

        result = SettlementService.add_commissions(
            settlement_id=settlement.id,
        )

        assert result.gross_sales == Decimal("250.00")
        assert result.commission_total == Decimal("17.50")
        assert result.adjustments_total == Decimal("-10.00")
        assert result.net_amount == Decimal("222.50")


@pytest.mark.django_db
class TestMarkSettlementReady:

    def test_pending_settlement_with_items_becomes_ready(
        self,
        active_store,
        order,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        SettlementItem.objects.create(
            settlement=settlement,
            commission=commission,
            gross_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        result = SettlementService.mark_ready(
            settlement_id=settlement.id,
        )

        assert result.status == SettlementStatus.READY

    def test_empty_settlement_cannot_become_ready(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        with pytest.raises(
            ValueError,
            match="Settlement must contain at least one item",
        ):
            SettlementService.mark_ready(
                settlement_id=settlement.id,
            )

    def test_ready_settlement_cannot_be_marked_ready_again(
        self,
        active_store,
        order,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        SettlementItem.objects.create(
            settlement=settlement,
            commission=commission,
            gross_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        SettlementService.mark_ready(
            settlement_id=settlement.id,
        )

        with pytest.raises(
            ValueError,
            match="Settlement must be pending",
        ):
            SettlementService.mark_ready(
                settlement_id=settlement.id,
            )

    def test_paid_settlement_cannot_become_ready(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PAID
        settlement.payment_reference = "PAY-001"
        settlement.paid_at = timezone.now()
        settlement.save()

        with pytest.raises(
            ValueError,
            match="Settlement must be pending",
        ):
            SettlementService.mark_ready(
                settlement_id=settlement.id,
            )


@pytest.mark.django_db
class TestStartProcessing:

    def test_ready_settlement_can_start_processing(
        self,
        active_store,
        order,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        SettlementItem.objects.create(
            settlement=settlement,
            commission=commission,
            gross_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        SettlementService.mark_ready(
            settlement_id=settlement.id,
        )

        result = SettlementService.start_processing(
            settlement_id=settlement.id,
        )

        assert result.status == SettlementStatus.PROCESSING

    def test_pending_settlement_cannot_start_processing(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        with pytest.raises(
            ValueError,
            match="Settlement must be ready",
        ):
            SettlementService.start_processing(
                settlement_id=settlement.id,
            )

    def test_paid_settlement_cannot_start_processing(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PAID
        settlement.payment_reference = "PAY-001"
        settlement.paid_at = timezone.now()
        settlement.save()

        with pytest.raises(
            ValueError,
            match="Settlement must be ready",
        ):
            SettlementService.start_processing(
                settlement_id=settlement.id,
            )

    def test_processing_settlement_cannot_start_processing_again(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PROCESSING
        settlement.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Settlement must be ready",
        ):
            SettlementService.start_processing(
                settlement_id=settlement.id,
            )


@pytest.mark.django_db
class TestMarkPaid:

    def test_processing_settlement_can_be_paid(
        self,
        active_store,
        order,
    ):
        commission = Commission.objects.create(
            order=order,
            store=active_store,
            rate=Decimal("7.00"),
            base_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=(timezone.now() - timedelta(days=1)).date(),
            period_end=(timezone.now() + timedelta(days=1)).date(),
        )

        SettlementItem.objects.create(
            settlement=settlement,
            commission=commission,
            gross_amount=Decimal("250.00"),
            commission_amount=Decimal("17.50"),
        )

        SettlementService.mark_ready(
            settlement_id=settlement.id,
        )

        SettlementService.start_processing(
            settlement_id=settlement.id,
        )

        result = SettlementService.mark_paid(
            settlement_id=settlement.id,
            payment_reference="PAY-2026-0001",
        )

        result.refresh_from_db()
        commission.refresh_from_db()

        assert result.status == SettlementStatus.PAID
        assert result.payment_reference == "PAY-2026-0001"
        assert result.paid_at is not None
        assert commission.status == "SETTLED"

    def test_payment_reference_is_required(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PROCESSING
        settlement.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Payment reference is required",
        ):
            SettlementService.mark_paid(
                settlement_id=settlement.id,
                payment_reference="",
            )

    def test_ready_settlement_cannot_be_paid(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.READY
        settlement.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Settlement must be processing",
        ):
            SettlementService.mark_paid(
                settlement_id=settlement.id,
                payment_reference="PAY-001",
            )

    def test_paid_settlement_cannot_be_paid_again(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PAID
        settlement.payment_reference = "PAY-001"
        settlement.paid_at = timezone.now()
        settlement.save()

        with pytest.raises(
            ValueError,
            match="Settlement must be processing",
        ):
            SettlementService.mark_paid(
                settlement_id=settlement.id,
                payment_reference="PAY-002",
            )
            
            
@pytest.mark.django_db
class TestDispute:

    def test_pending_settlement_can_be_disputed(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        result = SettlementService.dispute(
            settlement_id=settlement.id,
        )

        assert result.status == SettlementStatus.DISPUTED

    def test_ready_settlement_can_be_disputed(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.READY
        settlement.save(update_fields=["status"])

        result = SettlementService.dispute(
            settlement_id=settlement.id,
        )

        assert result.status == SettlementStatus.DISPUTED

    def test_processing_settlement_can_be_disputed(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PROCESSING
        settlement.save(update_fields=["status"])

        result = SettlementService.dispute(
            settlement_id=settlement.id,
        )

        assert result.status == SettlementStatus.DISPUTED

    def test_paid_settlement_cannot_be_disputed(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PAID
        settlement.payment_reference = "PAY-001"
        settlement.paid_at = timezone.now()
        settlement.save()

        with pytest.raises(
            ValueError,
            match="Paid settlement cannot be disputed",
        ):
            SettlementService.dispute(
                settlement_id=settlement.id,
            )

    def test_cancelled_settlement_cannot_be_disputed(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.CANCELLED
        settlement.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Cancelled settlement cannot be disputed",
        ):
            SettlementService.dispute(
                settlement_id=settlement.id,
            )
            
            
@pytest.mark.django_db
class TestCancelSettlement:

    def test_pending_settlement_can_be_cancelled(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        result = SettlementService.cancel(
            settlement_id=settlement.id,
        )

        assert result.status == SettlementStatus.CANCELLED

    def test_ready_settlement_can_be_cancelled(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.READY
        settlement.save(update_fields=["status"])

        result = SettlementService.cancel(
            settlement_id=settlement.id,
        )

        assert result.status == SettlementStatus.CANCELLED

    def test_processing_settlement_cannot_be_cancelled(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PROCESSING
        settlement.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Processing settlement cannot be cancelled",
        ):
            SettlementService.cancel(
                settlement_id=settlement.id,
            )

    def test_paid_settlement_cannot_be_cancelled(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.PAID
        settlement.payment_reference = "PAY-001"
        settlement.paid_at = timezone.now()
        settlement.save()

        with pytest.raises(
            ValueError,
            match="Paid settlement cannot be cancelled",
        ):
            SettlementService.cancel(
                settlement_id=settlement.id,
            )

    def test_disputed_settlement_cannot_be_cancelled(
        self,
        active_store,
    ):
        settlement = SettlementService.create_settlement(
            store_id=active_store.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 8),
        )

        settlement.status = SettlementStatus.DISPUTED
        settlement.save(update_fields=["status"])

        with pytest.raises(
            ValueError,
            match="Disputed settlement cannot be cancelled",
        ):
            SettlementService.cancel(
                settlement_id=settlement.id,
            )