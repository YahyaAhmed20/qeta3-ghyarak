from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from ..constants import OTPPurpose
from ..models import OTPChallenge


class OTPService:

    @staticmethod
    def generate_code() -> str:
        import secrets

        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def hash_code(code: str) -> str:
        return make_password(code)

    @staticmethod
    def verify_code(code: str, code_hash: str) -> bool:
        return check_password(code, code_hash)

    @staticmethod
    def create_challenge(user, purpose: OTPPurpose):
        OTPChallenge.objects.filter(
            user=user,
            purpose=purpose,
            verified_at__isnull=True,
        ).update(
            expires_at=timezone.now(),
        )

        code = OTPService.generate_code()

        challenge = OTPChallenge.objects.create(
            user=user,
            purpose=purpose,
            code_hash=OTPService.hash_code(code),
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
        )

        return challenge, code

    @staticmethod
    def verify_challenge(challenge: OTPChallenge, code: str) -> bool:
        with transaction.atomic():
            challenge = (
                OTPChallenge.objects
                .select_for_update()
                .get(pk=challenge.pk)
            )

            if challenge.verified_at is not None:
                return False

            if timezone.now() >= challenge.expires_at:
                return False

            if challenge.attempts >= challenge.max_attempts:
                return False

            challenge.attempts += 1

            if not OTPService.verify_code(code, challenge.code_hash):
                challenge.save(update_fields=["attempts"])
                return False

            challenge.verified_at = timezone.now()

            challenge.save(
                update_fields=[
                    "attempts",
                    "verified_at",
                ]
            )

            return True