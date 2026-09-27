from django.db import models, transaction
from django.utils import timezone

from apps.finance.models import CommissionRule


class CommissionRuleService:

    @staticmethod
    def _has_overlap(
        *,
        store_id,
        effective_from,
        effective_to,
        exclude_id=None,
    ):
        qs = CommissionRule.objects.filter(
            store_id=store_id,
            is_active=True,
        )

        if exclude_id:
            qs = qs.exclude(id=exclude_id)

        # Existing rule starts before the new rule ends.
        if effective_to is not None:
            qs = qs.filter(effective_from__lt=effective_to)

        # Existing rule either has no end
        # or ends after the new rule starts.
        qs = qs.filter(
            models.Q(effective_to__isnull=True)
            | models.Q(effective_to__gt=effective_from)
        )

        return qs.exists()

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        store,
        rate,
        effective_from=None,
        effective_to=None,
    ):
        if effective_from is None:
            effective_from = timezone.now()

        if cls._has_overlap(
            store_id=store.id,
            effective_from=effective_from,
            effective_to=effective_to,
        ):
            raise ValueError(
                "Commission rule overlaps with an existing active rule."
            )

        rule = CommissionRule(
            store=store,
            rate=rate,
            effective_from=effective_from,
            effective_to=effective_to,
        )

        rule.full_clean()
        rule.save()

        return rule