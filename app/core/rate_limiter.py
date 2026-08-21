import logging

from fastapi import HTTPException, status
from redis.client import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {current, ttl}
"""


def check_rate_limit(key: str, limit: int, window: int) -> None:

    try:
        current, ttl = redis_client.eval(RATE_LIMIT_SCRIPT, 1, key, window)

        if current > limit:
            raise HTTPException(
                status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
                detail="Too many requests",
                headers={"Retry-After": str(max(ttl, 1))},
            )

    except HTTPException:
        raise

    except RedisError:
        logger.exception("Rate limiter Redis unavailable. Failing open. key=%s", key)
