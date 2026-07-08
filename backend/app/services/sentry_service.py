"""Sentry integration for error tracking and monitoring."""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from typing import Optional


def init_sentry(dsn: Optional[str] = None, environment: str = "production") -> None:
    """Initialize Sentry for error tracking."""
    if not dsn:
        return
    
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=True,
    )


def capture_exception(exc: Exception, context: Optional[dict] = None) -> None:
    """Capture an exception in Sentry."""
    if sentry_sdk.Hub.current.client:
        with sentry_sdk.configure_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(exc)


def capture_message(message: str, level: str = "info", context: Optional[dict] = None) -> None:
    """Capture a message in Sentry."""
    if sentry_sdk.Hub.current.client:
        with sentry_sdk.configure_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)