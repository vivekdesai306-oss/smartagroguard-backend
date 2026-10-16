"""
AgroGuard Module 4 Operational Spray Safety Service
Enforces chemical application safety gates (wind drift limits and rainfastness windows)
directly feeding Module 3 Advisory Engine.
"""

from typing import List, Optional
from ..weather_config import (
    MAX_SPRAY_WIND_KMH,
    RAINFASTNESS_SAFETY_WINDOW_HOURS,
    MIN_RAINFAST_PRECIP_MM
)
from ..schemas.weather import (
    HourlyForecastPoint,
    WeatherSnapshot,
    WeatherAlertCreate,
    WeatherAlertType,
    SprayWeatherAssessment,
    WeatherTreatmentContext
)

class SpraySafetyService:
    """
    Evaluates weather suitability for chemical pesticide and fertilizer spraying.
    Prevents toxic off-target wind drift and wasteful rain washout.
    """

    @staticmethod
    def evaluate_spray_safety(
        current_wind_kmh: float,
        hourly_forecast: List[HourlyForecastPoint],
        required_rainfast_hours: float = RAINFASTNESS_SAFETY_WINDOW_HOURS
    ) -> SprayWeatherAssessment:
        blocking: List[str] = []

        # 1. Wind Drift Gate
        wind_safe = current_wind_kmh <= MAX_SPRAY_WIND_KMH
        if not wind_safe:
            blocking.append(
                f"HIGH_WIND_DRIFT_RISK: Current wind speed ({current_wind_kmh:.1f} km/h) exceeds the operational limit ({MAX_SPRAY_WIND_KMH} km/h). Chemical drift poses environmental and off-target crop burn hazard."
            )

        # 2. Rainfastness Gate
        rain_safe = True
        rain_expected = False
        hours_until_rain: Optional[float] = None

        if hourly_forecast:
            for idx, pt in enumerate(hourly_forecast):
                if pt.rainfall_mm >= MIN_RAINFAST_PRECIP_MM:
                    hours_until_rain = float(idx)
                    rain_expected = True
                    if hours_until_rain < required_rainfast_hours:
                        rain_safe = False
                        blocking.append(
                            f"RAINFASTNESS_LOCKOUT: Rain precipitation is forecast in {hours_until_rain:.1f} hour(s). Chemical foliar application requires at least {required_rainfast_hours} hours of dry weather to bond."
                        )
                    break

        is_safe = wind_safe and rain_safe

        return SprayWeatherAssessment(
            is_spray_safe=is_safe,
            wind_safe=wind_safe,
            rain_safe=rain_safe,
            rain_expected=rain_expected,
            hours_until_rain=hours_until_rain,
            blocking_reasons=blocking
        )

    @classmethod
    def build_treatment_context(
        cls,
        snapshot: WeatherSnapshot,
        hourly_forecast: List[HourlyForecastPoint],
        active_alerts: List[WeatherAlertCreate]
    ) -> WeatherTreatmentContext:
        """
        Builds the Module 3 integration context object.
        """
        safety = cls.evaluate_spray_safety(snapshot.wind_speed_kmh, hourly_forecast)
        alert_types = [a.alert_type for a in active_alerts if a.alert_type != WeatherAlertType.NONE]

        return WeatherTreatmentContext(
            is_spray_safe=safety.is_spray_safe,
            wind_speed_kmh=snapshot.wind_speed_kmh,
            rainfall_expected=safety.rain_expected,
            hours_until_rain=safety.hours_until_rain,
            weather_alerts=alert_types,
            blocking_reasons=safety.blocking_reasons,
            source_status=snapshot.source_status,
            is_fallback=snapshot.is_fallback
        )
