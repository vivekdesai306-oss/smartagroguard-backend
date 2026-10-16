"""
FastAPI Router for Multi-Criteria Optimal Harvest Readiness & Post-Harvest Advisory
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional

from ..schemas.harvest import HarvestEvaluationRequest, HarvestReadinessResponse
from ..services.harvest_readiness_service import HarvestReadinessService

router = APIRouter(prefix="/api/v1/harvest", tags=["Optimal Harvest Readiness & Storage"])

@router.post("/evaluate", response_model=HarvestReadinessResponse)
def evaluate_harvest_readiness(req: HarvestEvaluationRequest):
    """
    Evaluates the 5-Pillar Harvest Decision Criteria:
    1. R6 Black Layer Formation
    2. Cumulative GDD Target (>= 1450 °C-days)
    3. Grain Field Moisture (<= 20%)
    4. Chemical PHI Withholding Clearance
    5. 72-Hour Rain-Free Meteorological Window
    """
    return HarvestReadinessService.evaluate_harvest_readiness(
        farm_id=req.farm_id,
        das=req.das,
        growth_stage=req.growth_stage,
        cumulative_gdd=req.cumulative_gdd or 1480.0,
        estimated_grain_moisture_pct=req.estimated_grain_moisture_pct or 18.5,
        last_chemical_spray_date=req.last_chemical_spray_date,
        last_chemical_id=req.last_chemical_id,
        forecast_rain_next_3_days_mm=req.forecast_rain_next_3_days_mm or 0.0
    )
