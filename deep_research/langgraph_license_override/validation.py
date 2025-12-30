"""Noop license middleware - bypasses all license checks"""

import structlog
from typing import Any

logger = structlog.stdlib.get_logger(__name__)

# Optional attributes that may be imported by other modules
CUSTOMER_ID = None
CUSTOMER_NAME = None


class LicenseStatus:
    """Mock license status that always passes"""
    def __init__(self):
        self.is_enterprise = True
        self.allows_custom_auth = True
        self.has_license = True
        self.is_valid = True
        self.allows_self_hosting = True


async def get_license_status() -> LicenseStatus:
    """Always return a valid license status without checking"""
    return LicenseStatus()


async def get_or_refresh_license() -> LicenseStatus:
    """Always return a valid license status without checking"""
    return LicenseStatus()


def decode_license_jwt(_: str) -> dict[str, Any]:
    """Noop - never called, but defined to prevent import errors"""
    return {}


def plus_features_enabled() -> bool:
    """Always return True to enable all features"""
    return True


async def check_license_periodically(_: int = 60) -> None:
    """
    Periodically re-verify the license.
    Noop version - does nothing.
    """
    await logger.ainfo(
        "This is a noop license middleware. No license check is performed."
    )
    return None

