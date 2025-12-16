"""
Rate Limiting Service.
Tracks API usage and enforces limits to prevent quota exhaustion.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time

from ..database.db import get_db_session
from ..database.models import APIUsage, User, UserRole
try:
    from src.infra.redis_client import redis_client
except Exception:  # pragma: no cover
    redis_client = None


class RateLimiter:
    """
    Rate limiter for external API calls.
    Tracks usage per user and globally.
    """
    
    # Default limits per day
    LIMITS = {
        "groq": {
            UserRole.ANALYST: 100,
            UserRole.MANAGER: 200,
            UserRole.EXECUTIVE: 500,
            UserRole.ADMIN: 1000,
            "global": 5000  # Total across all users
        },
        "tavily": {
            UserRole.ANALYST: 50,
            UserRole.MANAGER: 100,
            UserRole.EXECUTIVE: 200,
            UserRole.ADMIN: 500,
            "global": 1000
        }
    }
    
    # In-memory cache for fast lookups (reset daily)
    _cache: Dict[str, Dict] = {}
    _cache_date: Optional[datetime] = None
    
    @classmethod
    def _get_cache_key(cls, api_name: str, user_id: Optional[int] = None) -> str:
        """Generate cache key."""
        if user_id:
            return f"{api_name}:user:{user_id}"
        return f"{api_name}:global"
    
    @classmethod
    def _reset_cache_if_needed(cls):
        """Reset cache at start of new day."""
        today = datetime.utcnow().date()
        if cls._cache_date != today:
            cls._cache = {}
            cls._cache_date = today
    
    @classmethod
    def check_limit(cls, api_name: str, user_id: Optional[int] = None, user_role: UserRole = UserRole.ANALYST) -> Tuple[bool, int, int]:
        """
        Check if user is within rate limits.
        
        Returns:
            (allowed: bool, current_count: int, limit: int)
        """
        cls._reset_cache_if_needed()
        
        if api_name not in cls.LIMITS:
            return True, 0, 9999  # Unknown API, allow
        
        limits = cls.LIMITS[api_name]
        
        # Get user limit
        user_limit = limits.get(user_role, limits.get(UserRole.ANALYST, 100))
        global_limit = limits.get("global", 5000)
        
        # Check cache first
        user_key = cls._get_cache_key(api_name, user_id)
        global_key = cls._get_cache_key(api_name)
        
        user_count = cls._cache.get(user_key, 0)
        global_count = cls._cache.get(global_key, 0)
        
        # Check limits
        if user_id and user_count >= user_limit:
            return False, user_count, user_limit
        
        if global_count >= global_limit:
            return False, global_count, global_limit
        
        return True, user_count, user_limit
    
    @classmethod
    def record_usage(cls, api_name: str, user_id: Optional[int] = None) -> bool:
        """
        Record an API call.
        
        Returns:
            True if recorded successfully, False if limit would be exceeded.
        """
        cls._reset_cache_if_needed()
        
        # Update cache
        user_key = cls._get_cache_key(api_name, user_id) if user_id else None
        global_key = cls._get_cache_key(api_name)
        
        if user_key:
            cls._cache[user_key] = cls._cache.get(user_key, 0) + 1
        cls._cache[global_key] = cls._cache.get(global_key, 0) + 1
        
        # Record to database (async in production)
        try:
            with get_db_session() as db:
                usage = APIUsage(
                    user_id=user_id,
                    api_name=api_name,
                    calls_count=1,
                    date=datetime.utcnow()
                )
                db.add(usage)
        except Exception:
            pass  # Don't fail on DB errors
        
        return True
    
    @classmethod
    def get_usage_stats(cls, user_id: Optional[int] = None, api_name: Optional[str] = None) -> Dict:
        """Get usage statistics."""
        cls._reset_cache_if_needed()
        
        stats = {}
        
        for api in cls.LIMITS.keys():
            if api_name and api != api_name:
                continue
            
            user_key = cls._get_cache_key(api, user_id) if user_id else None
            global_key = cls._get_cache_key(api)
            
            stats[api] = {
                "user_calls": cls._cache.get(user_key, 0) if user_key else None,
                "global_calls": cls._cache.get(global_key, 0),
                "user_limit": cls.LIMITS[api].get(UserRole.ANALYST, 100),
                "global_limit": cls.LIMITS[api].get("global", 5000)
            }
        
        return stats
    
    @classmethod
    def get_remaining(cls, api_name: str, user_id: Optional[int] = None, user_role: UserRole = UserRole.ANALYST) -> int:
        """Get remaining calls for an API."""
        allowed, current, limit = cls.check_limit(api_name, user_id, user_role)
        return max(0, limit - current)


def rate_limited(api_name: str):
    """
    Decorator to rate limit a function.
    
    Usage:
        @rate_limited("groq")
        def call_groq_api(user_id, ...):
            ...
    """
    def decorator(func):
        def wrapper(*args, user_id: Optional[int] = None, user_role: UserRole = UserRole.ANALYST, **kwargs):
            # Check limit
            allowed, current, limit = RateLimiter.check_limit(api_name, user_id, user_role)
            
            if not allowed:
                raise RateLimitExceeded(
                    f"Rate limit exceeded for {api_name}: {current}/{limit} calls today"
                )
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Record usage
            RateLimiter.record_usage(api_name, user_id)
            
            return result
        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


# Lightweight Redis-backed token bucket for Groq calls
def allow_groq_call(user_id: Optional[str] = None, rate: int = 5, burst: int = 10) -> bool:
    """
    Simple token bucket limiter using Redis (or in-memory fallback).
    rate: tokens per second, burst: max tokens.
    """
    if redis_client is None:
        return True

    key = f"rl:groq:{user_id or 'global'}"
    now = int(time.time())
    raw = redis_client.get(key)

    if raw:
        try:
            tokens_str, ts_str = raw.split(":")
            tokens, ts = int(tokens_str), int(ts_str)
        except ValueError:
            tokens, ts = burst, now
    else:
        tokens, ts = burst, now

    tokens = min(burst, tokens + (now - ts) * rate)
    if tokens <= 0:
        return False

    tokens -= 1
    redis_client.setex(key, 60, f"{tokens}:{now}")
    return True
