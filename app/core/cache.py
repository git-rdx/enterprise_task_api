import json

from app.core.redis import redis_client


def set_cache(key: str, value, ttl: int = 300):
    redis_client.setex(key, ttl, json.dumps(value))


def get_cache(key: str):
    value = redis_client.get(key)

    if value is None:
        return None

    return json.loads(value)


def delete_cache(key: str):
    redis_client.delete(key)


def get_cache_version(key: str) -> int:

    value = redis_client.get(key)

    if value is None:
        redis_client.set(key, 1)
        return 1

    return int(value)


def increment_cache_version(key: str) -> int:

    return redis_client.incr(key)
