"""
Pydantic Schemas for Multi-Criteria Optimal Harvest Readiness & Post-Harvest Advisory
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class HarvestEvaluationRequest(BaseModel):
    farm_id: Optional[str] = None
    das: int = Field(default=105, ge=0, description="Days After Sowing")
    growth_stage: str = Field(default="R6", description="Growth stage (R5 or R6)")
    cumulative_gdd: Optional[float] = Field(1480.0, description="Cumulative Growing Degree Days (°C-days)")
    estimated_grain_moisture_pct: Optional[float] = Field(18.5, description="Grain kernel moisture content %")
    last_chemical_spray_date: Optional[str] = Field(None, description="Date of last pesticide application (YYYY-MM-DD)")
    last_chemical_id: Optional[str] = Field(None, description="Chemical ID used")
    forecast_rain_next_3_days_mm: Optional[float] = Field(0.0, description="Expected precipitation over next 72 hours (mm)")

class HarvestCriterionStatus(BaseModel):
    criterion_name: str
    is_passed: bool
    current_value: Any
    target_threshold: Any
    status_label: str
    explanation: str

class HarvestReadinessResponse(BaseModel):
    farm_id: Optional[str] = None
    overall_status: str  # GREEN_LIGHT_HARVEST / CHEMICAL_PHI_HOLD / WEATHER_RAIN_HOLD / IMMATURE_GRAIN_HOLD
    is_ready_for_harvest: bool
    harvest_readiness_score_pct: float
    headline: str
    plain_summary: str
    criteria_breakdown: List[HarvestCriterionStatus]
    phi_countdown_days_remaining: int
    post_harvest_storage_protocol: List[str]
    optimal_harvest_window: str
