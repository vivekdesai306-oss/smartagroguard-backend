from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Weather Alert Enums (SRS §1.3.1.4 & Table 1.6.7) ---
class WeatherAlertType(str, Enum):
    FROST = "Frost"
    HEAVY_RAIN = "Heavy Rain"
    HIGH_HUMIDITY = "High Humidity"
    NONE = "None"

class WeatherSeverity(str, Enum):
    CRITICAL = "CRITICAL"    # Immediate danger to crop (Frost, Flash Heavy Rain)
    WARNING = "WARNING"      # Requires proactive adjustment (Heavy rain warning)
    ADVISORY = "ADVISORY"    # Informational notice (Frost advisory, Fungal incubation watch)
    NORMAL = "NORMAL"        # Optimal atmospheric conditions

class WeatherSourceStatus(str, Enum):
    LIVE = "LIVE"
    CACHE = "CACHE"
    FALLBACK = "FALLBACK"
    UNAVAILABLE = "UNAVAILABLE"

# --- Meteorological Forecast & Snapshot Schemas ---
class HourlyForecastPoint(BaseModel):
    timestamp: datetime
    temperature_c: float
    relative_humidity_percent: float
    rainfall_mm: float = 0.0
    precipitation_mm: float = 0.0
    wind_speed_kmh: float
    wind_gust_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    precipitation_probability_percent: Optional[float] = None
    weather_code: Optional[int] = None
    is_day: Optional[bool] = None

class DailyForecastSummary(BaseModel):
    date: str
    temp_min_c: float
    temp_max_c: float
    total_rainfall_mm: float
    avg_humidity_percent: int
    dominant_condition: str
    frost_risk: str

class WeatherSnapshot(BaseModel):
    observed_at: datetime
    temperature_c: float
    relative_humidity_percent: float
    rainfall_last_24h_mm: float
    rainfall_last_48h_mm: float
    wind_speed_kmh: float
    wind_gust_kmh: Optional[float] = None
    source: str
    source_status: WeatherSourceStatus
    is_fallback: bool = False

class WeatherForecast(BaseModel):
    farm_id: str
    generated_at: datetime
    timezone: str = "Asia/Kolkata"
    source: str
    source_status: WeatherSourceStatus
    is_fallback: bool = False
    hourly: List[HourlyForecastPoint]
    forecast_hours: int = Field(..., ge=48)

class FarmWeatherLocation(BaseModel):
    farm_id: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    district: str
    state: str
    agro_climatic_zone: str
    timezone: str = "Asia/Kolkata"

# --- SRS Table 1.6.7 Weather Alert Schemas ---
class WeatherAlertCreate(BaseModel):
    farm_id: str
    alert_type: WeatherAlertType
    severity: WeatherSeverity
    alert_date: datetime
    title: str
    message: str
    trigger_value: Optional[float] = None
    trigger_unit: Optional[str] = None
    threshold_value: Optional[float] = None
    guidance: List[str] = []
    is_active: bool = True
    source: str
    source_status: WeatherSourceStatus
    forecast_timestamp: Optional[datetime] = None

class WeatherAlertOut(WeatherAlertCreate):
    alert_id: str = Field(..., max_length=10)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WeatherRiskAssessment(BaseModel):
    alert_type: WeatherAlertType
    severity: WeatherSeverity
    risk_score: Optional[float] = None
    reasons: List[str]
    guidance: List[str]
    valid_from: datetime
    valid_until: datetime

# --- Operational Spray & Treatment Context (Module 3 Hand-off) ---
class SprayWeatherAssessment(BaseModel):
    is_spray_safe: bool
    wind_safe: bool
    rain_safe: bool
    rain_expected: bool
    hours_until_rain: Optional[float] = None
    blocking_reasons: List[str] = []

class WeatherTreatmentContext(BaseModel):
    is_spray_safe: bool
    wind_speed_kmh: float
    rainfall_expected: bool
    hours_until_rain: Optional[float] = None
    weather_alerts: List[WeatherAlertType] = []
    blocking_reasons: List[str] = []
    source_status: WeatherSourceStatus
    is_fallback: bool = False

# --- Comprehensive Overview Schema ---
class FarmWeatherOverviewOut(BaseModel):
    farm_id: str
    farm_address: str
    coordinates: Dict[str, float]
    weather: Dict[str, Any]
    forecast: Dict[str, Any]
    alerts: List[WeatherAlertOut]
    hourly_forecast_48h: Optional[List[HourlyForecastPoint]] = None
    daily_forecast_7d: Optional[List[DailyForecastSummary]] = None
    spray_safety: SprayWeatherAssessment
    source: Dict[str, Any]
