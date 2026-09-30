import pytest

from apps.accounts.models import User


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        phone="+201001234581",
        role="CUSTOMER",
        is_active=True,
    )


@pytest.fixture
def another_customer(db):
    return User.objects.create_user(
        phone="+201001234582",
        role="CUSTOMER",
        is_active=True,
    )