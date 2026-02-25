from __future__ import annotations

import logging
import time
import uuid
from functools import partial

import anyio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings
from app.core.security import get_current_user_optional
from app.services.audit_service import log_http_audit_event

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    _SKIP_PREFIXES = ("/docs", "/openapi", "/redoc", "/favicon.ico")

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        started_at = time.perf_counter()
        status_code = 500
        response = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            if not settings.AUDIT_ENABLED or self._should_skip(request.url.path):
                continue_logging = False
            else:
                continue_logging = True

            if continue_logging:
                actor_user_id = getattr(request.state, "audit_actor_user_id", None)
                if actor_user_id is None:
                    maybe_user = get_current_user_optional(request)
                    actor_user_id = maybe_user["user_id"] if maybe_user else None

                duration_ms = int((time.perf_counter() - started_at) * 1000)
                event_type = self._classify_event_type(request.url.path, status_code)
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                metadata = {"duration_ms": duration_ms}
                writer = partial(
                    log_http_audit_event,
                    event_type=event_type,
                    actor_user_id=actor_user_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    metadata=metadata,
                )

                try:
                    await anyio.to_thread.run_sync(writer)
                except Exception as exc:
                    logger.exception("Audit middleware failed to log event: %s", exc)

    def _should_skip(self, path: str) -> bool:
        if not path.startswith("/api/"):
            return True
        return path.startswith(self._SKIP_PREFIXES)

    def _classify_event_type(self, path: str, status_code: int) -> str:
        if path == "/api/v1/auth/login":
            return "auth.login.failed" if status_code >= 400 else "auth.login.success"
        if status_code == 403:
            return "auth.access.denied"
        return "http.request"
