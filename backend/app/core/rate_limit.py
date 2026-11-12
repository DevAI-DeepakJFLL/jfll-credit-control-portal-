"""
In-Memory IP Rate Limiter for Jet Freight Logistics Credit Control CRM.
Centralized rate limiting utility shared across API automation routes.
"""
import os
import time
import threading
from collections import defaultdict
from fastapi import Request, HTTPException

_rate_limit_lock = threading.Lock()
_ip_request_timestamps = defaultdict(list)
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"

def check_rate_limit(request: Request, limit: int = RATE_LIMIT_PER_MINUTE, window: int = 60):
    ip = get_client_ip(request)
    now = time.time()
    with _rate_limit_lock:
        timestamps = _ip_request_timestamps[ip]
        cutoff = now - window
        active_timestamps = [t for t in timestamps if t > cutoff]
        _ip_request_timestamps[ip] = active_timestamps
        if len(active_timestamps) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Maximum 30 requests per minute allowed."
            )
        _ip_request_timestamps[ip].append(now)

        # Periodic memory cleanup if many distinct client IPs accumulate
        if len(_ip_request_timestamps) > 1000:
            dead_ips = [k for k, v in _ip_request_timestamps.items() if not v or v[-1] <= cutoff]
            for k in dead_ips:
                del _ip_request_timestamps[k]
