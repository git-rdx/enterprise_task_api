import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Keep imports grouped and alphabetized for linting.
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

        except Exception:
            logger.exception(
                "Unhandled request exception | request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )

            raise

        duration = time.perf_counter() - start_time

        logger.info(
            "Request completed | "
            "request_id=%s method=%s path=%s "
            "status=%s duration=%.4fs",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        response.headers["X-Request-ID"] = request_id

        return response
