"""
AgroGuard Module 4 Centralized Weather Configuration
Contains all threshold constants for biological stress, operational spray safety,
and cache lifetimes.
"""

# Frost Risk Thresholds (°C)
FROST_FREEZE_C = 0.0
FROST_CRITICAL_C = 3.0
FROST_ADVISORY_C = 7.0

# Precipitation Thresholds (mm)
HEAVY_RAIN_WARNING_24H_MM = 50.0
HEAVY_RAIN_CRITICAL_24H_MM = 75.0
HEAVY_RAIN_HOURLY_RATE_MM = 15.0

# Fungal Incubation Thresholds (Puccinia sorghi / Exserohilum turcicum)
HIGH_HUMIDITY_PERCENT = 90.0
HIGH_HUMIDITY_MIN_DURATION_HOURS = 8
FUNGAL_TEMP_MIN_C = 18.0
FUNGAL_TEMP_MAX_C = 30.0

# Operational Spray Safety Thresholds
MAX_SPRAY_WIND_KMH = 18.0
RAINFASTNESS_SAFETY_WINDOW_HOURS = 4.0
MIN_RAINFAST_PRECIP_MM = 1.0

# System & Cache Parameters
WEATHER_CACHE_TTL_SECONDS = 600  # 10 minutes (600s)
FORECAST_HOURS_REQUIRED = 48
CACHE_TARGET_LATENCY_MS = 20.0
