from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1)
def get_redis_client() -> Optional[object]:
    """Return None when Redis is not used/available."""
    return None

