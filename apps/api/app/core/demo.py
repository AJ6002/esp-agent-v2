"""Demo account identification."""

from __future__ import annotations

DEMO_EMAIL_DOMAIN = "example.com"


def is_demo_account(email: str) -> bool:
    """Identify reserved domain accounts used by seed data."""

    return email.strip().casefold().endswith(f"@{DEMO_EMAIL_DOMAIN}")
