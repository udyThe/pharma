import time
from typing import Optional

from .redis_client import get_redis_client


class RedisCache:
    """Simple cache facade using Redis when available, else in-memory."""

    def __init__(self):
        self.client = get_redis_client()
        self._memory = {}

    def get(self, key: str) -> Optional[str]:
        if self.client:
            val = self.client.get(key)
            return val
        entry = self._memory.get(key)
        if not entry:
            return None
        value, exp = entry
        if exp and exp < time.time():
            self._memory.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl_seconds: int = 1800):
        if self.client:
            self.client.setex(key, ttl_seconds, value)
            return
        exp = time.time() + ttl_seconds if ttl_seconds else None
        self._memory[key] = (value, exp)


redis_cache = RedisCache()

