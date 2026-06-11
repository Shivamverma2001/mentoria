import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)

_sentry_enabled = False


def init_sentry() -> bool:
    global _sentry_enabled

    if not settings.sentry_dsn:
        logger.info("Sentry DSN not set — observability disabled")
        _sentry_enabled = False
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
        enable_tracing=True,
    )
    _sentry_enabled = True
    logger.info("Sentry initialized for environment=%s", settings.sentry_environment)
    return True


def sentry_enabled() -> bool:
    return _sentry_enabled
