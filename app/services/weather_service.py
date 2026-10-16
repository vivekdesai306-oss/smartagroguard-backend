import logging
import time
import urllib.request
import urllib.error
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from ..weather_config import (
    WEATHER_CACHE_TTL_SECONDS,
    FORECAST_HOURS_REQUIRED,
    FROST_FREEZE_C,
    FROST_CRITICAL_C,
    FROST_ADVISORY_C,
    MAX_SPRAY_WIND_KMH,
    RAINFASTNESS_SAFETY_WINDOW_HOURS,
    MIN_RAINFAST_PRECIP_MM
)
from .weather_cache_service import WeatherCacheService
from ..schemas.weather import (
    HourlyForecastPoint,
    DailyForecastSummary,
    WeatherSnapshot,
    WeatherForecast,
    WeatherSourceStatus
)

logger = logging.getLogger("agroguard.weather_service")

# Climatic normal fallbacks for Indian agro-climatic zones if external API is unreachable
CLIMATIC_NORMALS = {
    "KHARIF": {
        "temperature_c": 31.0,
        "humidity_percent": 74,
        "rainfall_mm": 5.2,
        "wind_speed_kmh": 12.0,
        "solar_radiation": "Moderate-High",
        "frost_risk": "None",
        "weather_condition": "Partly Cloudy with Monsoon Moisture"
    },
    "RABI": {
        "temperature_c": 22.0,
        "humidity_percent": 55,
        "rainfall_mm": 0.0,
        "wind_speed_kmh": 8.0,
        "solar_radiation": "High Clear Sky",
        "frost_risk": "Low to Moderate in Northern Belts",
        "weather_condition": "Clear Sky / Mild Winter"
    },
    "SUMMER": {
        "temperature_c": 38.5,
        "humidity_percent": 38,
        "rainfall_mm": 0.0,
        "wind_speed_kmh": 14.0,
        "solar_radiation": "Very High",
        "frost_risk": "None",
        "weather_condition": "Hot & Dry / High Evaporation"
    }
}

class WeatherService:
    """
    Agro-meteorological Service for Smart AgroGuard.
    Fetches live weather observations and 48-hour hourly forecasts from Open-Meteo API.
    Guarantees zero-crash operation via dual-tier caching and IMD Agro-Climatic Normal fallbacks.
    """

    @classmethod
    def get_weather_for_gps(
        cls,
        latitude: Optional[float],
        longitude: Optional[float],
        season: str = "KHARIF"
    ) -> Dict[str, Any]:
        """
        Legacy compatibility method for crop scanning (Module 2).
        Returns localized snapshot.
        """
        snapshot, _ = cls.get_weather_snapshot(latitude, longitude, farm_id="legacy")
        return {
            "temperature_c": snapshot.temperature_c,
            "humidity_percent": int(snapshot.relative_humidity_percent),
            "rainfall_mm": snapshot.rainfall_last_24h_mm,
            "wind_speed_kmh": snapshot.wind_speed_kmh,
            "solar_radiation": "Optimal",
            "frost_risk": "Critical Frost-Risk" if snapshot.temperature_c <= FROST_CRITICAL_C else ("Frost Advisory" if snapshot.temperature_c <= FROST_ADVISORY_C else "None"),
            "weather_condition": "Live Meteorological Conditions" if not snapshot.is_fallback else "Climatic Normal Fallback",
            "source": snapshot.source,
            "source_status": snapshot.source_status.value,
            "is_fallback": snapshot.is_fallback
        }

    @classmethod
    def get_weather_snapshot(
        cls,
        latitude: Optional[float],
        longitude: Optional[float],
        farm_id: str = "farm_default",
        db: Optional[Any] = None
    ) -> Tuple[WeatherSnapshot, List[HourlyForecastPoint]]:
        """
        Fetches or retrieves cached snapshot and 48-hour hourly forecast.
        """
        lat = latitude if latitude is not None else 22.7758
        lon = longitude if longitude is not None else 73.6149
        cache_key = WeatherCacheService.get_cache_key(farm_id)

        # 1. Check valid cache
        cached = WeatherCacheService.get(cache_key)
        if cached:
            try:
                hourly = [HourlyForecastPoint(**pt) for pt in cached.get("hourly", [])]
                snapshot = WeatherSnapshot(**cached.get("snapshot", {}))
                snapshot.source_status = WeatherSourceStatus.CACHE
                return snapshot, hourly
            except Exception as e:
                logger.warning(f"Failed to deserialize cached weather: {e}")

        # 2. Query Live API
        live_res = cls._fetch_live_open_meteo(lat, lon, farm_id)
        if live_res:
            snapshot, hourly, daily = live_res
            # Save in cache
            cache_payload = {
                "snapshot": snapshot.dict(),
                "hourly": [h.dict() for h in hourly],
                "daily": [d.dict() for d in daily],
                "lat": lat,
                "lon": lon
            }
            WeatherCacheService.set(cache_key, cache_payload, ttl_seconds=WEATHER_CACHE_TTL_SECONDS)
            return snapshot, hourly

        # 3. Fallback to Climatological Normals
        logger.warning(f"Live Weather API unreachable for ({lat}, {lon}). Falling back to Agro-Climatic Normals.")
        snapshot, hourly = cls._generate_climatic_fallback(farm_id, lat, lon)
        return snapshot, hourly

    @classmethod
    def _fetch_live_open_meteo(
        cls,
        lat: float,
        lon: float,
        farm_id: str
    ) -> Optional[Tuple[WeatherSnapshot, List[HourlyForecastPoint], List[DailyForecastSummary]]]:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,wind_gusts_10m,weather_code&"
            f"hourly=temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m,wind_gusts_10m,is_day&"
            f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&"
            f"forecast_days=3&past_days=2&timezone=Asia%2FKolkata"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AgroGuard-Platform/1.0"})
            with urllib.request.urlopen(req, timeout=3.5) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    return cls._parse_open_meteo_payload(payload, farm_id)
        except Exception as e:
            logger.warning(f"Open-Meteo API query error: {str(e)}")
            return None

    @classmethod
    def _parse_open_meteo_payload(
        cls,
        data: Dict[str, Any],
        farm_id: str
    ) -> Tuple[WeatherSnapshot, List[HourlyForecastPoint], List[DailyForecastSummary]]:
        curr = data.get("current", {})
        hourly_data = data.get("hourly", {})
        daily_data = data.get("daily", {})

        now_dt = datetime.now()

        # Parse Hourly array
        times = hourly_data.get("time", [])
        temps = hourly_data.get("temperature_2m", [])
        rhs = hourly_data.get("relative_humidity_2m", [])
        precips = hourly_data.get("precipitation", [])
        winds = hourly_data.get("wind_speed_10m", [])
        gusts = hourly_data.get("wind_gusts_10m", [])
        w_codes = hourly_data.get("weather_code", [])
        is_days = hourly_data.get("is_day", [])

        # Find current hour index
        current_idx = 0
        now_iso_prefix = now_dt.strftime("%Y-%m-%dT%H")
        for i, t_str in enumerate(times):
            if t_str.startswith(now_iso_prefix):
                current_idx = i
                break

        # Calculate recent rainfall from past 24/48 hours
        start_24h = max(0, current_idx - 24)
        start_48h = max(0, current_idx - 48)
        rain_24h = sum(float(precips[k]) for k in range(start_24h, current_idx) if k < len(precips))
        rain_48h = sum(float(precips[k]) for k in range(start_48h, current_idx) if k < len(precips))

        # Extract 48 contiguous forecast hours starting from current_idx
        forecast_points: List[HourlyForecastPoint] = []
        for j in range(current_idx, min(len(times), current_idx + 48)):
            t_val = datetime.fromisoformat(times[j])
            temp_c = float(temps[j]) if j < len(temps) and temps[j] is not None else 25.0
            rh_pct = float(rhs[j]) if j < len(rhs) and rhs[j] is not None else 65.0
            p_mm = float(precips[j]) if j < len(precips) and precips[j] is not None else 0.0
            w_kmh = float(winds[j]) if j < len(winds) and winds[j] is not None else 8.0
            g_kmh = float(gusts[j]) if j < len(gusts) and gusts[j] is not None else None
            code = int(w_codes[j]) if j < len(w_codes) and w_codes[j] is not None else 0
            is_d = bool(is_days[j]) if j < len(is_days) and is_days[j] is not None else True

            # Determine spray safety for hour
            spray_ok = (w_kmh <= MAX_SPRAY_WIND_KMH) and (p_mm < MIN_RAINFAST_PRECIP_MM)

            forecast_points.append(
                HourlyForecastPoint(
                    timestamp=t_val,
                    temperature_c=round(temp_c, 1),
                    relative_humidity_percent=round(rh_pct, 1),
                    rainfall_mm=round(p_mm, 1),
                    precipitation_mm=round(p_mm, 1),
                    wind_speed_kmh=round(w_kmh, 1),
                    wind_gust_kmh=round(g_kmh, 1) if g_kmh is not None else None,
                    weather_code=code,
                    is_day=is_d
                )
            )

        # Parse 7-day daily summaries
        daily_summaries: List[DailyForecastSummary] = []
        d_times = daily_data.get("time", [])
        d_maxs = daily_data.get("temperature_2m_max", [])
        d_mins = daily_data.get("temperature_2m_min", [])
        d_rains = daily_data.get("precipitation_sum", [])
        for k in range(len(d_times)):
            t_min = float(d_mins[k]) if k < len(d_mins) and d_mins[k] is not None else 20.0
            t_max = float(d_maxs[k]) if k < len(d_maxs) and d_maxs[k] is not None else 32.0
            r_sum = float(d_rains[k]) if k < len(d_rains) and d_rains[k] is not None else 0.0
            frost_str = "Critical Frost-Risk" if t_min <= FROST_CRITICAL_C else ("Frost Advisory" if t_min <= FROST_ADVISORY_C else "None")
            daily_summaries.append(
                DailyForecastSummary(
                    date=d_times[k],
                    temp_min_c=round(t_min, 1),
                    temp_max_c=round(t_max, 1),
                    total_rainfall_mm=round(r_sum, 1),
                    avg_humidity_percent=65,
                    dominant_condition="Clear / Optimal" if r_sum == 0 else "Rain Showers",
                    frost_risk=frost_str
                )
            )

        current_temp = float(curr.get("temperature_2m", temps[current_idx] if current_idx < len(temps) else 25.0))
        current_rh = float(curr.get("relative_humidity_2m", rhs[current_idx] if current_idx < len(rhs) else 65.0))
        current_wind = float(curr.get("wind_speed_10m", winds[current_idx] if current_idx < len(winds) else 10.0))
        current_gust = float(curr.get("wind_gusts_10m")) if curr.get("wind_gusts_10m") is not None else None

        snapshot = WeatherSnapshot(
            observed_at=now_dt,
            temperature_c=round(current_temp, 1),
            relative_humidity_percent=round(current_rh, 1),
            rainfall_last_24h_mm=round(rain_24h, 1),
            rainfall_last_48h_mm=round(rain_48h, 1),
            wind_speed_kmh=round(current_wind, 1),
            wind_gust_kmh=round(current_gust, 1) if current_gust is not None else None,
            source="open-meteo",
            source_status=WeatherSourceStatus.LIVE,
            is_fallback=False
        )

        return snapshot, forecast_points, daily_summaries

    @classmethod
    def _generate_climatic_fallback(
        cls,
        farm_id: str,
        lat: float,
        lon: float
    ) -> Tuple[WeatherSnapshot, List[HourlyForecastPoint]]:
        """
        Deterministic, zero-crash fallback based on Indian Agro-Climatic Normals.
        Explicitly marked with is_fallback = True.
        """
        now = datetime.now()
        # Fallback profile (Middle Gujarat / Normal Zone 13)
        base_temp = 28.5
        base_rh = 70.0
        base_wind = 10.0

        hourly: List[HourlyForecastPoint] = []
        for h in range(48):
            step_dt = now + timedelta(hours=h)
            # Diurnal temperature curve simulation
            hour_of_day = step_dt.hour
            temp_offset = -4.0 if 3 <= hour_of_day <= 6 else (4.0 if 13 <= hour_of_day <= 16 else 0.0)
            sim_temp = round(base_temp + temp_offset, 1)
            sim_rh = round(base_rh - (temp_offset * 2.0), 1)

            hourly.append(
                HourlyForecastPoint(
                    timestamp=step_dt,
                    temperature_c=sim_temp,
                    relative_humidity_percent=sim_rh,
                    rainfall_mm=0.0,
                    precipitation_mm=0.0,
                    wind_speed_kmh=base_wind,
                    weather_code=1,
                    is_day=6 <= hour_of_day <= 18
                )
            )

        snapshot = WeatherSnapshot(
            observed_at=now,
            temperature_c=base_temp,
            relative_humidity_percent=base_rh,
            rainfall_last_24h_mm=0.0,
            rainfall_last_48h_mm=0.0,
            wind_speed_kmh=base_wind,
            wind_gust_kmh=None,
            source="agro_climatic_normal",
            source_status=WeatherSourceStatus.FALLBACK,
            is_fallback=True
        )

        return snapshot, hourly
