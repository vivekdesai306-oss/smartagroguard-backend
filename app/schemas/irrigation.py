"""
Pydantic Schemas for FAO-56 Penman-Monteith Evapotranspiration and Smart Irrigation Engine
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class IrrigationCalculationRequest(BaseModel):
    farm_id: Optional[str] = None
    area_acres: float = Field(default=1.0, ge=0.1, description="Field size in acres")
    soil_type: str = Field(default="Sandy Loam (Goradu)", description="Soil texture type")
    das: int = Field(default=45, ge=0, le=140, description="Days After Sowing")
    temperature_c: Optional[float] = Field(30.0, description="Mean daily temperature in °C")
    humidity_percent: Optional[int] = Field(65, description="Relative humidity %")
    wind_speed_kmh: Optional[float] = Field(8.0, description="Wind speed in km/h")
    solar_radiation_mj: Optional[float] = Field(18.5, description="Daily solar radiation in MJ/m2/day")
    rainfall_7d_mm: Optional[float] = Field(0.0, description="Cumulative rainfall over past 7 days (mm)")
    irrigation_method: str = Field(default="Drip", description="Drip | Furrow | Sprinkler")
    drip_flow_rate_lph: Optional[float] = Field(4.0, description="Emitter flow rate in Liters/Hour")
    simulated_soil_vwc_pct: Optional[float] = Field(None, description="Optional telemetry sensor VWC%")

class SoilWaterStatusOut(BaseModel):
    soil_type: str
    field_capacity_pct: float
    wilting_point_pct: float
    current_estimated_vwc_pct: float
    management_allowed_depletion_pct: float
    moisture_deficit_status: str  # OPTIMAL / MODERATE_DEFICIT / CRITICAL_STRESS / WATERLOGGED
    is_irrigation_needed: bool

class IrrigationCalculationResponse(BaseModel):
    das: int
    growth_stage_code: str
    growth_stage_name: str
    kc_crop_coefficient: float
    et0_reference_mm_per_day: float
    etc_crop_water_demand_mm_per_day: float
    daily_water_liters_per_acre: float
    total_water_volume_liters: float
    soil_status: SoilWaterStatusOut
    irrigation_method: str
    recommended_runtime_hours: float
    stunting_triage_note: str
    action_guidance: str
    calculated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SoilTelemetryIngestRequest(BaseModel):
    farm_id: str
    sensor_id: str = "PROBE_01"
    depth_cm: int = 15
    volumetric_water_content_pct: float = Field(..., ge=0.0, le=100.0)
    soil_temperature_c: Optional[float] = None
    battery_level_pct: Optional[float] = 100.0
