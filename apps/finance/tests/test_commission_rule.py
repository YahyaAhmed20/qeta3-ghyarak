from datetime import timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.finance.models import CommissionRule


@pytest.mark.django_db
def test_commission_rule_accepts_valid_rate(active_store):
    now = timezone.now()

    rule = CommissionRule(
        store=active_store,
        rate="7.00",
        effective_from=now,
    )

    rule.full_clean()

    assert rule.rate == Decimal("7.00")


@pytest.mark.django_db
def test_commission_rule_rejects_negative_rate(active_store):
    rule = CommissionRule(
        store=active_store,
        rate="-1.00",
        effective_from=timezone.now(),
    )

    with pytest.raises(ValidationError):
        rule.full_clean()


@pytest.mark.django_db
def test_commission_rule_rejects_rate_above_100(active_store):
    rule = CommissionRule(
        store=active_store,
        rate="100.01",
        effective_from=timezone.now(),
    )

    with pytest.raises(ValidationError):
        rule.full_clean()


@pytest.mark.django_db
def test_commission_rule_rejects_invalid_effective_period(
    active_store,
):
    now = timezone.now()

    rule = CommissionRule(
        store=active_store,
        rate="7.00",
        effective_from=now,
        effective_to=now,
    )

    with pytest.raises(ValidationError):
        rule.full_clean()


@pytest.mark.django_db
def test_commission_rule_allows_open_ended_period(
    active_store,
):
    rule = CommissionRule(
        store=active_store,
        rate="7.00",
        effective_from=timezone.now(),
        effective_to=None,
    )

    rule.full_clean()


@pytest.mark.django_db
def test_commission_rule_allows_valid_period(
    active_store,
):
    now = timezone.now()

    rule = CommissionRule(
        store=active_store,
        rate="7.00",
        effective_from=now,
        effective_to=now + timedelta(days=30),
    )

    rule.full_clean()