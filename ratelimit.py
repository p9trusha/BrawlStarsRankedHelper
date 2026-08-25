import threading
import time
from collections import defaultdict, deque
from functools import wraps

from flask import jsonify, request

WINDOW_SECONDS = 60.0
MAX_REQUESTS = 120

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def allow(ip: str) -> bool:
    now = time.monotonic()
    with _lock:
        dq = _hits[ip]
        cutoff = now - WINDOW_SECONDS
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= MAX_REQUESTS:
            return False
        dq.append(now)
        if len(_hits) > 10000:
            for key in list(_hits.keys()):
                if not _hits[key]:
                    del _hits[key]
        return True


def rate_limited(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        ip = client_ip()
        if not allow(ip):
            return (
                jsonify({"error": "Слишком много запросов. Подожди немного."}),
                429,
            )
        return fn(*args, **kwargs)

    return wrapper
