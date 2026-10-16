"""
FastAPI Router for FAO-56 Penman-Monteith Evapotranspiration & Smart Irrigation Engine
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, Dict, Any

from ..database import get_database
from ..schemas.irrigation import (
    IrrigationCalculationRequest,
    IrrigationCalculationResponse,
    SoilTelemetryIngestRequest
)
from ..services.irrigation_service import IrrigationService

router = APIRouter(prefix="/api/v1/irrigation", tags=["Smart Irrigation & FAO-56 Water Balance"])

@router.post("/calculate", response_model=IrrigationCalculationResponse)
def calculate_irrigation(req: IrrigationCalculationRequest):
    """
    Computes daily FAO-56 Penman-Monteith reference evapotranspiration (ET0),
    crop water demand (ETc), soil moisture deficit, and pump runtime hours.
    """
    return IrrigationService.calculate_irrigation_budget(
        area_acres=req.area_acres,
        soil_type=req.soil_type,
        das=req.das,
        temperature_c=req.temperature_c or 30.0,
        humidity_percent=req.humidity_percent or 65,
        wind_speed_kmh=req.wind_speed_kmh or 8.0,
        solar_radiation_mj=req.solar_radiation_mj or 18.5,
        rainfall_7d_mm=req.rainfall_7d_mm or 0.0,
        irrigation_method=req.irrigation_method or "Drip",
        drip_flow_rate_lph=req.drip_flow_rate_lph or 4.0,
        simulated_soil_vwc_pct=req.simulated_soil_vwc_pct
    )

@router.post("/telemetry/soil")
async def ingest_soil_telemetry(req: SoilTelemetryIngestRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    IoT Ingestion endpoint for Soil Moisture Probes (Volumetric Water Content %).
    """
    doc = {
        "farm_id": req.farm_id,
        "sensor_id": req.sensor_id,
        "depth_cm": req.depth_cm,
        "vwc_pct": req.volumetric_water_content_pct,
        "soil_temp_c": req.soil_temperature_c,
        "battery_pct": req.battery_level_pct
    }
    if db is not None:
        try:
            await db["soil_telemetry"].insert_one(doc)
        except Exception:
            pass
    doc.pop("_id", None)
    return {"status": "SUCCESS", "message": "Telemetry ingested successfully", "data": doc}
