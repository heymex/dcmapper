import os
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "120"))

_request_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def apply_security_headers(response) -> None:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    # strict-origin-when-cross-origin sends origin on HTTPS tile requests (required by many tile CDNs).
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' https://unpkg.com; "
        "script-src 'self' https://unpkg.com; "
        "img-src 'self' data: https://*.basemaps.cartocdn.com; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )


def check_rate_limit(request: Request) -> JSONResponse | None:
    if not request.url.path.startswith("/api/"):
        return None

    now = time.time()
    bucket = _request_buckets[_client_key(request)]

    while bucket and (now - bucket[0]) > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please retry shortly."},
        )

    bucket.append(now)
    return None
