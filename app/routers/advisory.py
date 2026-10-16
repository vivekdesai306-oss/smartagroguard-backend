from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any

from ..schemas import Module3InputContract, Module3Output
from ..services.advisory_service import AdvisoryService
from ..database import get_database

router = APIRouter(prefix="/api/v1/advisory", tags=["Module 3: Advisory & Treatment Engine"])

@router.post("/evaluate", response_model=Module3Output)
async def evaluate_advisory(input_contract: Module3InputContract):
    """
    Evaluates evidence-based farm advisory and treatment recommendation for a given input contract.
    Enforces strict safety validation gates (wind drift, rainfastness, chemical conflicts, PHI).
    """
    try:
        output = await AdvisoryService.generate_farm_advisory(input_contract)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advisory evaluation error: {str(e)}")

@router.post("/scan/{scan_id}", response_model=Module3Output)
async def evaluate_scan_advisory(scan_id: str, scouting_observations: Optional[List[str]] = None):
    """
    Evaluates advisory for an existing scan record in the database and updates its module3_advisory snapshot.
    """
    db = get_database()
    scan_record = await db["scans"].find_one({"scan_id": scan_id})
    if not scan_record:
        raise HTTPException(status_code=404, detail=f"Scan record {scan_id} not found.")

    # Reconstruct Module3InputContract from stored scan record
    growth = scan_record.get("growth") or {}
    height = scan_record.get("height") or {}
    health = scan_record.get("health") or {}
    env = scan_record.get("environment") or {}
    disease_log = scan_record.get("disease_log") or {}
    
    # Query farm ground truth
    farm_id = scan_record.get("farm_id")
    farm_record = await db["farms"].find_one({"farm_id": farm_id}) if farm_id else None

    # Module 4 Weather Intelligence Integration (Spray Safety & Rainfastness)
    wind_val = env.get("wind_speed_kmh", 8.0)
    hours_rain = env.get("hours_until_rain", 24.0)
    if farm_record:
        lat = farm_record.get("entered_latitude") or farm_record.get("latitude")
        lon = farm_record.get("entered_longitude") or farm_record.get("longitude")
        try:
            from ..services.weather_service import WeatherService
            from ..services.spray_safety_service import SpraySafetyService
            snapshot, hourly = WeatherService.get_weather_snapshot(lat, lon, farm_id=farm_id or "default", db=db)
            safety = SpraySafetyService.evaluate_spray_safety(snapshot.wind_speed_kmh, hourly)
            wind_val = snapshot.wind_speed_kmh
            if safety.hours_until_rain is not None:
                hours_rain = safety.hours_until_rain
        except Exception:
            pass

    input_contract = Module3InputContract(
        diagnostics={
            "scan_id": scan_id,
            "visual_week": growth.get("visual_week", "Week 5"),
            "visual_confidence": growth.get("visual_confidence", 0.85),
            "calculated_das": scan_record.get("day_count", 30),
            "measured_height_cm": height.get("measured_height_cm"),
            "expected_height_range_str": height.get("expected_range_str", "50–80 cm"),
            "height_status": height.get("height_status", "WITHIN_EXPECTED"),
            "detected_disease": disease_log.get("detected_disease", "Healthy"),
            "disease_confidence": disease_log.get("confidence_score", 0.95),
            "review_status": disease_log.get("review_status", "Auto-confirmed"),
            "scouting_observations": scouting_observations or []
        },
        environment={
            "rainfall_mm": env.get("rainfall_mm", 0.0),
            "temperature_c": env.get("temperature_c", 28.0),
            "humidity_percent": env.get("humidity_percent", 65),
            "wind_speed_kmh": wind_val,
            "hours_until_rain": hours_rain,
            "forecast_rain_volume_mm": 0.0,
            "season": env.get("season", "KHARIF"),
            "district": farm_record.get("district", "Panchmahal") if farm_record else "Panchmahal",
            "agro_climatic_zone": "Middle Gujarat Agro-Climatic Zone III"
        },
        farm={
            "farm_id": farm_id or "farm_default",
            "uid": farm_record.get("uid", "user_default") if farm_record else "user_default",
            "crop_type": scan_record.get("crop_type", "Corn"),
            "variety": farm_record.get("variety", "GAYMH-1") if farm_record else "GAYMH-1",
            "soil_type": farm_record.get("soil_type", "Sandy Loam (Goradu)") if farm_record else "Sandy Loam (Goradu)",
            "farm_area_acres": float(farm_record.get("farm_area", "1.0").split()[0]) if (farm_record and farm_record.get("farm_area")) else 1.0,
            "sowing_date": scan_record.get("sowing_date", "2026-06-01")
        }
    )

    output = await AdvisoryService.generate_farm_advisory(input_contract)

    # Persist module3_advisory embedded snapshot to database
    await db["scans"].update_one(
        {"scan_id": scan_id},
        {"$set": {"module3_advisory": output.dict()}}
    )

    return output
