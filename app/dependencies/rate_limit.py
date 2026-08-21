from typing import Callable

from fastapi import Request

from app.core.rate_limiter import check_rate_limit


def rate_limit(limit: int, window: int) -> Callable:

    def dependency(request: Request) -> None:

        client_ip = request.client.host if request.client else "unknown"

        key = f"rate_limit:{request.url.path}:{client_ip}"

        check_rate_limit(key=key, limit=limit, window=window)

    return dependency
