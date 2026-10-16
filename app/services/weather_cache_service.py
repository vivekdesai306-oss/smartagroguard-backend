"""
AgroGuard Module 4 Weather Cache Service
Provides an in-memory / pluggable cache with TTL for weather observations and forecasts.
Guarantees sub-20ms p95 latency on cache hits.
"""

import time
import logging
from typing import Optional, Dict, Any
from ..weather_config import WEATHER_CACHE_TTL_SECONDS

logger = logging.getLogger("agroguard.weather_cache")

class WeatherCacheService:
    # Key -> {"data": Any, "cached_at": float, "expires_at": float}
    _cache: Dict[str, Dict[str, Any]] = {}
    _latencies: list = []

    @classmethod
    def get_cache_key(cls, farm_id: str) -> str:
        return f"weather:farm:{farm_id}:48h"

    @classmethod
    def get_geo_key(cls, lat: float, lon: float) -> str:
        return f"weather:geo:{round(lat, 3)}:{round(lon, 3)}"

    @classmethod
    def get(cls, key: str) -> Optional[Dict[str, Any]]:
        t_start = time.perf_counter()
        entry = cls._cache.get(key)
        if not entry:
            return None
        
        now = time.time()
        if now > entry.get("expires_at", 0):
            # Expired
            cls._cache.pop(key, None)
            return None
        
        latency_ms = (time.perf_counter() - t_start) * 1000.0
        cls._latencies.append(latency_ms)
        if len(cls._latencies) > 1000:
            cls._latencies.pop(0)

        return entry.get("data")

    @classmethod
    def set(cls, key: str, data: Dict[str, Any], ttl_seconds: int = WEATHER_CACHE_TTL_SECONDS) -> None:
        now = time.time()
        cls._cache[key] = {
            "data": data,
            "cached_at": now,
            "expires_at": now + ttl_seconds
        }

    @classmethod
    def invalidate(cls, key: str) -> None:
        cls._cache.pop(key, None)

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()
        cls._latencies.clear()

    @classmethod
    def get_p95_latency_ms(cls) -> float:
        if not cls._latencies:
            return 0.0
        sorted_l = sorted(cls._latencies)
        idx = int(len(sorted_l) * 0.95)
        return round(sorted_l[min(idx, len(sorted_l) - 1)], 2)
