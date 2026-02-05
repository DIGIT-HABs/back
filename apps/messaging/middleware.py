"""
JWT authentication middleware for WebSocket connections.
Allows consumers to receive scope['user'] when client sends Bearer token
via query string (?token=xxx) or Authorization header.
"""

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


def get_token_from_scope(scope):
    """Extract JWT from WebSocket scope (query string or path or headers)."""
    # 1) scope['query_string'] (ASGI standard)
    query_string = scope.get("query_string", b"")
    if isinstance(query_string, bytes):
        query_string = query_string.decode("utf-8", errors="replace")
    # 2) Fallback: some servers put full path+query in path only
    if not query_string:
        path = scope.get("path", "") or ""
        if "?" in path:
            query_string = path.split("?", 1)[1]
    if query_string:
        parsed = parse_qs(query_string)
        tokens = parsed.get("token", [])
        if tokens:
            return tokens[0].strip()
    # Headers: Authorization: Bearer ACCESS_TOKEN
    headers = dict(
        (k.decode().lower() if isinstance(k, bytes) else k.lower(), v.decode() if isinstance(v, bytes) else v)
        for k, v in scope.get("headers", [])
    )
    auth = headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


@database_sync_to_async
def get_user_from_token(token):
    """Validate JWT and return User or AnonymousUser (sync, run in thread)."""
    if not token:
        return AnonymousUser()
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication

        auth = JWTAuthentication()
        validated_token = auth.get_validated_token(token)
        return auth.get_user(validated_token)
    except Exception as e:
        logger.debug("WebSocket JWT auth failed: %s", e)
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    ASGI middleware that sets scope['user'] from JWT token
    (query string ?token=xxx or header Authorization: Bearer xxx).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            token = get_token_from_scope(scope)
            if not token:
                qs = scope.get("query_string")
                path = scope.get("path", "")
                logger.warning(
                    "WebSocket JWT: no token (path=%r, query_string=%r)",
                    path,
                    qs[:100] if isinstance(qs, bytes) and len(qs) > 100 else qs,
                )
            else:
                logger.info("WebSocket JWT: token found, validating...")
            scope["user"] = await get_user_from_token(token)
        return await self.app(scope, receive, send)
