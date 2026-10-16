"""
AgroGuard Module 4 REST API Router
Exposes weather intelligence, biological crop risk alerts, spray safety validations,
and farmer notification delivery audit trails.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from ..database import get_database
from ..schemas.weather import (
    FarmWeatherOverviewOut,
    WeatherSnapshot,
    WeatherForecast,
    WeatherAlertOut,
    SprayWeatherAssessment,
    HourlyForecastPoint
)
from ..services.weather_service import WeatherService
from ..services.weather_alert_engine import WeatherAlertEngine
from ..services.spray_safety_service import SpraySafetyService
from ..services.notification_service import NotificationService

logger = logging.getLogger("agroguard.routers.weather")

router = APIRouter(prefix="/api/v1/weather", tags=["Module 4: Weather Intelligence & Alerts"])

async def _get_farm_context(db: AsyncIOMotorDatabase, farm_id: str) -> Dict[str, Any]:
    """
    Retrieves farm coordinates and address from MongoDB, or falls back to defaults.
    """
    farm = None
    if db is not None:
        farm = await db["farms"].find_one({"farm_id": farm_id})
    
    if farm:
        lat = float(farm.get("entered_latitude") or farm.get("latitude", 22.7758))
        lon = float(farm.get("entered_longitude") or farm.get("longitude", 73.6149))
        address = farm.get("farm_address") or f"{farm.get('taluka', 'Godhra')}, {farm.get('district', 'Panchmahal')}, Gujarat"
        return {
            "farm_id": farm_id,
            "latitude": lat,
            "longitude": lon,
            "farm_address": address,
            "user_profile": {"mobile_no": farm.get("mobile_no"), "email": farm.get("email")}
        }
    
    # Graceful fallback for demo or test farm IDs
    return {
        "farm_id": farm_id,
        "latitude": 22.7758,
        "longitude": 73.6149,
        "farm_address": "Vavdi, Godhra, Panchmahal, Gujarat",
        "user_profile": {"mobile_no": "9876543210", "email": "farmer@agroguard.com"}
    }

@router.get("/farm/{farm_id}/overview", response_model=FarmWeatherOverviewOut)
async def get_farm_weather_overview(
    farm_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Primary Weather Dashboard Endpoint.
    Aggregates live weather observations, 48h forecast, active biological hazard alerts,
    operational spray safety clearance, and data provenance.
    """
    farm_ctx = await _get_farm_context(db, farm_id)
    lat = farm_ctx["latitude"]
    lon = farm_ctx["longitude"]

    # 1. Fetch live or cached snapshot and hourly forecast
    snapshot, hourly = WeatherService.get_weather_snapshot(lat, lon, farm_id=farm_id, db=db)

    # 2. Evaluate biological hazards against corn agronomic thresholds
    raw_alerts = WeatherAlertEngine.generate_alerts(
        farm_id=farm_id,
        hourly=hourly,
        source=snapshot.source,
        source_status=snapshot.source_status
    )

    # 3. Synchronize with database and dispatch deduplicated farmer notifications
    active_alerts = await WeatherAlertEngine.sync_and_save_alerts(
        db=db,
        farm_id=farm_id,
        alerts=raw_alerts,
        user_profile=farm_ctx.get("user_profile")
    )

    # 4. Evaluate operational spray safety window
    spray_safety = SpraySafetyService.evaluate_spray_safety(
        current_wind_kmh=snapshot.wind_speed_kmh,
        hourly_forecast=hourly
    )

    return FarmWeatherOverviewOut(
        farm_id=farm_id,
        farm_address=farm_ctx["farm_address"],
        coordinates={"latitude": lat, "longitude": lon},
        weather={
            "temperature_c": snapshot.temperature_c,
            "relative_humidity_percent": int(snapshot.relative_humidity_percent),
            "rainfall_last_24h_mm": snapshot.rainfall_last_24h_mm,
            "rainfall_last_48h_mm": snapshot.rainfall_last_48h_mm,
            "wind_speed_kmh": snapshot.wind_speed_kmh,
            "wind_gust_kmh": snapshot.wind_gust_kmh
        },
        forecast={"hours": len(hourly)},
        alerts=active_alerts,
        hourly_forecast_48h=hourly,
        spray_safety=spray_safety,
        source={
            "status": snapshot.source_status.value,
            "provider": snapshot.source,
            "is_fallback": snapshot.is_fallback
        }
    )

@router.get("/farm/{farm_id}/current", response_model=WeatherSnapshot)
async def get_current_weather(
    farm_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns real-time atmospheric observation snapshot for the farm.
    """
    farm_ctx = await _get_farm_context(db, farm_id)
    snapshot, _ = WeatherService.get_weather_snapshot(
        farm_ctx["latitude"],
        farm_ctx["longitude"],
        farm_id=farm_id,
        db=db
    )
    return snapshot

@router.get("/farm/{farm_id}/forecast", response_model=WeatherForecast)
async def get_weather_forecast(
    farm_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns continuous 48-hour hourly forecasting matrix for the farm.
    """
    farm_ctx = await _get_farm_context(db, farm_id)
    snapshot, hourly = WeatherService.get_weather_snapshot(
        farm_ctx["latitude"],
        farm_ctx["longitude"],
        farm_id=farm_id,
        db=db
    )
    return WeatherForecast(
        farm_id=farm_id,
        generated_at=datetime.now(),
        timezone="Asia/Kolkata",
        source=snapshot.source,
        source_status=snapshot.source_status,
        is_fallback=snapshot.is_fallback,
        hourly=hourly,
        forecast_hours=len(hourly)
    )

@router.get("/farm/{farm_id}/alerts", response_model=List[WeatherAlertOut])
async def get_farm_alerts(
    farm_id: str,
    active_only: bool = Query(True, description="Filter for only active alerts"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Fetches Table 1.6.7 weather alerts for the farm.
    """
    if active_only:
        return await WeatherAlertEngine.get_active_alerts_for_farm(db, farm_id)
    return await WeatherAlertEngine.get_all_alerts_for_farm(db, farm_id, limit=limit)

@router.get("/farm/{farm_id}/spray-safety", response_model=SprayWeatherAssessment)
async def get_farm_spray_safety(
    farm_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Evaluates weather safety clearance for chemical spraying (Wind drift and Rainfastness lockout).
    Used by Module 3 Treatment Gate.
    """
    farm_ctx = await _get_farm_context(db, farm_id)
    snapshot, hourly = WeatherService.get_weather_snapshot(
        farm_ctx["latitude"],
        farm_ctx["longitude"],
        farm_id=farm_id,
        db=db
    )
    return SpraySafetyService.evaluate_spray_safety(
        current_wind_kmh=snapshot.wind_speed_kmh,
        hourly_forecast=hourly
    )

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_weather_alert(
    alert_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Allows a farmer to acknowledge and dismiss an active weather alert.
    """
    success = await WeatherAlertEngine.acknowledge_alert(db, alert_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather alert '{alert_id}' not found or already acknowledged."
        )
    return {"status": "ACKNOWLEDGED", "alert_id": alert_id, "acknowledged_at": datetime.now().isoformat()}

@router.get("/farm/{farm_id}/notifications")
async def get_notification_logs(
    farm_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns audit trail of dispatched SMS/Email notification delivery logs.
    """
    return await NotificationService.get_delivery_logs(db, farm_id)
