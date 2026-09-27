from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.finance.models import CommissionRule
from apps.finance.services.commission_rule import CommissionRuleService


@pytest.mark.django_db
def test_create_commission_rule(active_store):
    now = timezone.now()

    rule = CommissionRuleService.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=now,
    )

    assert rule.pk is not None
    assert rule.store == active_store
    assert rule.rate == Decimal("7.00")
    assert rule.effective_from == now
    assert rule.effective_to is None
    assert rule.is_active is True


@pytest.mark.django_db
def test_reject_overlapping_rules_for_same_store(active_store):
    now = timezone.now()

    CommissionRuleService.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=now,
        effective_to=now + timedelta(days=30),
    )

    with pytest.raises(ValueError, match="overlaps"):
        CommissionRuleService.create(
            store=active_store,
            rate=Decimal("8.00"),
            effective_from=now + timedelta(days=10),
            effective_to=now + timedelta(days=40),
        )


@pytest.mark.django_db
def test_allow_adjacent_rules_for_same_store(active_store):
    now = timezone.now()
    first_end = now + timedelta(days=30)

    CommissionRuleService.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=now,
        effective_to=first_end,
    )

    second = CommissionRuleService.create(
        store=active_store,
        rate=Decimal("8.00"),
        effective_from=first_end,
        effective_to=first_end + timedelta(days=30),
    )

    assert second.rate == Decimal("8.00")


@pytest.mark.django_db
def test_open_ended_rule_blocks_future_rule(active_store):
    now = timezone.now()

    CommissionRuleService.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=now,
    )

    with pytest.raises(ValueError, match="overlaps"):
        CommissionRuleService.create(
            store=active_store,
            rate=Decimal("8.00"),
            effective_from=now + timedelta(days=30),
        )


@pytest.mark.django_db
def test_future_rule_does_not_overlap_past_rule(active_store):
    now = timezone.now()
    first_end = now + timedelta(days=30)

    CommissionRuleService.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=now,
        effective_to=first_end,
    )

    second = CommissionRuleService.create(
        store=active_store,
        rate=Decimal("8.00"),
        effective_from=first_end + timedelta(seconds=1),
    )

    assert second.rate == Decimal("8.00")


@pytest.mark.django_db
def test_rules_for_different_stores_can_overlap(active_store, finance_owner, db):
    from apps.stores.models import Store

    second_owner = finance_owner.__class__.objects.create_user(
        phone="+201001234581",
        role="SELLER_OWNER",
        is_active=True,
    )

    second_store = Store.objects.create(
        owner=second_owner,
        name="Second Finance Store",
        slug="second-finance-store",
        phone="+201001234581",
        address="Test Address",
        city="Suez",
        status="ACTIVE",
        is_verified=True,
    )

    now = timezone.now()

    first = CommissionRuleService.create(
        store=active_store,
        rate=Decimal("7.00"),
        effective_from=now,
    )

    second = CommissionRuleService.create(
        store=second_store,
        rate=Decimal("8.00"),
        effective_from=now + timedelta(days=1),
    )

    assert first.store_id != second.store_id