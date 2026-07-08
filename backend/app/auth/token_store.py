"""Server-side, revocable refresh-token store backed by Redis.

Refresh tokens are opaque random strings (JTI) stored in Redis with a TTL.
This makes them revocable: logout or "revoke all" simply deletes the key,
and a stolen refresh token can be invalidated immediately. The short-lived
access JWT stays stateless; only the long-lived refresh token is tracked.

If Redis is unavailable the store degrades to a non-persistent in-memory
dict so the app still boots (refresh tokens just won't survive a restart
and can't be revoked) — this keeps local/dev usable without a Redis server.
"""
from __future__ import annotations

import os
import secrets
import threading
import time
from typing import Optional

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
REFRESH_TTL_SECONDS = int(os.getenv("REFRESH_TOKEN_TTL_SECONDS", "604800"))  # 7 days

_KEY_PREFIX = "refresh:"
_user_prefix = "user_refresh:"
_jti_prefix = "jti:"


class TokenStore:
    def __init__(self, url: str = REDIS_URL):
        self._local: dict[str, float] = {}
        self._local_jti: dict[str, int] = {}
        self._lock = threading.Lock()
        self._client: Optional[redis.Redis] = None
        self._using_redis = False
        try:
            client = redis.Redis.from_url(
                url, socket_connect_timeout=2, socket_timeout=2, decode_responses=True
            )
            client.ping()
            self._client = client
            self._using_redis = True
        except Exception:
            # Degrade gracefully without Redis.
            self._client = None
            self._using_redis = False

    @property
    def backend(self) -> str:
        return "redis" if self._using_redis else "memory"

    def create(self, user_id: int) -> str:
        """Store a new refresh token for a user and return its opaque value."""
        jti = secrets.token_urlsafe(32)
        key = f"{_KEY_PREFIX}{user_id}:{jti}"
        if self._using_redis:
            self._client.set(key, "1", ex=REFRESH_TTL_SECONDS)
            # Reverse index jti -> user_id for O(1) lookup on refresh.
            self._client.set(f"{_jti_prefix}{jti}", user_id, ex=REFRESH_TTL_SECONDS)
            # Track per-user tokens so we can revoke all at once.
            self._client.sadd(f"{_user_prefix}{user_id}", jti)
            self._client.expire(f"{_user_prefix}{user_id}", REFRESH_TTL_SECONDS)
        else:
            with self._lock:
                self._local[key] = time.time() + REFRESH_TTL_SECONDS
                self._local_jti[jti] = user_id
        return jti

    def lookup_user(self, jti: str) -> Optional[int]:
        """Reverse lookup: which user owns this refresh token (or None)."""
        if self._using_redis:
            val = self._client.get(f"{_jti_prefix}{jti}")
            return int(val) if val is not None else None
        with self._lock:
            return self._local_jti.get(jti)

    def is_valid(self, user_id: int, jti: str) -> bool:
        key = f"{_KEY_PREFIX}{user_id}:{jti}"
        if self._using_redis:
            return bool(self._client.exists(key))
        with self._lock:
            exp = self._local.get(key)
            if exp is None:
                return False
            if exp < time.time():
                self._local.pop(key, None)
                self._local_jti.pop(jti, None)
                return False
            return True

    def revoke(self, user_id: int, jti: str) -> None:
        key = f"{_KEY_PREFIX}{user_id}:{jti}"
        if self._using_redis:
            self._client.delete(key)
            self._client.delete(f"{_jti_prefix}{jti}")
            self._client.srem(f"{_user_prefix}{user_id}", jti)
        else:
            with self._lock:
                self._local.pop(key, None)
                self._local_jti.pop(jti, None)

    def revoke_all(self, user_id: int) -> None:
        """Revoke every refresh token for a user (global logout / lockout)."""
        if self._using_redis:
            jtis = self._client.smembers(f"{_user_prefix}{user_id}")
            for jti in jtis:
                self._client.delete(f"{_KEY_PREFIX}{user_id}:{jti}")
                self._client.delete(f"{_jti_prefix}{jti}")
            self._client.delete(f"{_user_prefix}{user_id}")
        else:
            with self._lock:
                for key in list(self._local.keys()):
                    if key.startswith(f"{_KEY_PREFIX}{user_id}:"):
                        jti = key.split(":", 2)[-1]
                        self._local.pop(key, None)
                        self._local_jti.pop(jti, None)


# Module-level singleton (imported across the app).
token_store = TokenStore()
