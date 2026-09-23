import uuid

from django.conf import settings
from django.db import models

from ..constants import OTPPurpose


class OTPChallenge(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otp_challenges",
    )

    purpose = models.CharField(
        max_length=30,
        choices=OTPPurpose.choices,
    )

    code_hash = models.CharField(max_length=128)

    expires_at = models.DateTimeField()

    attempts = models.PositiveSmallIntegerField(default=0)

    max_attempts = models.PositiveSmallIntegerField(default=5)

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "purpose", "created_at"],
            ),
            models.Index(
                fields=["expires_at"],
            ),
        ]

    def __str__(self):
        return f"{self.user.phone} - {self.purpose}"