from fastapi import APIRouter
import logging

from ..schemas import (
    LocationVerifyRequest,
    LocationVerifyResponse,
    SuitabilityEvaluateRequest,
    SuitabilityReportOut
)
from ..services.suitability_service import SuitabilityService
from ..data.maize_suitability_data import (
    AGRO_CLIMATIC_ZONES,
    DISTRICT_MAIZE_DATABASE,
    STATE_MAIZE_DEFAULTS
)

logger = logging.getLogger("agroguard.routers.suitability")
router = APIRouter(prefix="/api/v1/suitability", tags=["Suitability & Location Validation"])

@router.post("/verify-location", response_model=LocationVerifyResponse)
def verify_location(req: LocationVerifyRequest):
    """
    Question 1: Is the farmer actually at the location they entered?
    Computes distance between farm entered coordinates and GPS navigation coordinates.
    """
    res = SuitabilityService.checkLocationVerification(
        entered_lat=req.entered_latitude,
        entered_lon=req.entered_longitude,
        gps_lat=req.gps_latitude,
        gps_lon=req.gps_longitude,
        threshold_meters=req.threshold_meters or 1000.0
    )
    return res

@router.post("/evaluate", response_model=SuitabilityReportOut)
@router.post("/check-suitability", response_model=SuitabilityReportOut)
def evaluate_suitability(req: SuitabilityEvaluateRequest):
    """
    Runs full multi-tier suitability engine:
    1. GPS Location verification
    2. Geographical Area Suitability (Village -> District -> Zone -> State -> National)
    3. Season suitability
    4. Sowing date vs regional window comparison
    5. Unified agricultural decision (GREEN / YELLOW / RED)
    """
    report = SuitabilityService.evaluate_farm_suitability(
        state=req.state,
        district=req.district,
        taluka=req.taluka,
        village=req.village,
        entered_lat=req.entered_latitude,
        entered_lon=req.entered_longitude,
        gps_lat=req.gps_latitude,
        gps_lon=req.gps_longitude,
        season=req.season or "KHARIF",
        sowing_date=req.sowing_date
    )
    return report

@router.get("/regions")
def get_supported_regions():
    """
    Returns lists of Indian states, districts, agro-climatic zones, and sample presets
    for easy testing of Cases A, B, C, D, and E in frontend UI.
    """
    states_list = sorted(list(STATE_MAIZE_DEFAULTS.keys()))
    districts_list = []
    for key, d in DISTRICT_MAIZE_DATABASE.items():
        districts_list.append({
            "state": d["state"],
            "district": d["district"],
            "is_suitable": d["is_suitable"],
            "zone_key": d["zone_key"],
            "seasons": list(d.get("seasons", {}).keys())
        })

    # Standard presets representing the 5 Critical Cases from the specification
    case_presets = [
        {
            "case_id": "CASE_A",
            "title": "Case A: Ideal Cultivation (All Pass)",
            "description": "GPS matching, suitable area (Panchmahal, Gujarat), Kharif season, sowing within window (June 28), maize photo.",
            "state": "Gujarat",
            "district": "Panchmahal",
            "taluka": "Godhra",
            "village": "Vavdi",
            "entered_lat": 22.7758,
            "entered_lon": 73.6149,
            "gps_lat": 22.7762,
            "gps_lon": 73.6155,  # ~75m away (MATCH)
            "season": "KHARIF",
            "sowing_date": "2026-06-28",
            "expected_outcome": "GREEN_SUITABLE with normal disease diagnosis"
        },
        {
            "case_id": "CASE_B",
            "title": "Case B: Sowing Time Not Ideal (Late Sowing)",
            "description": "GPS matching, suitable area, but sown on August 10 (outside June 15 - July 15 Kharif window). Shows Sowing Alert but STILL allows crop diagnosis.",
            "state": "Gujarat",
            "district": "Panchmahal",
            "taluka": "Godhra",
            "village": "Vavdi",
            "entered_lat": 22.7758,
            "entered_lon": 73.6149,
            "gps_lat": 22.7760,
            "gps_lon": 73.6150,  # ~25m away (MATCH)
            "season": "KHARIF",
            "sowing_date": "2026-08-10", # 26 days late
            "expected_outcome": "YELLOW_TIME_NOT_IDEAL with crop image analysis enabled"
        },
        {
            "case_id": "CASE_C",
            "title": "Case C: Area Not Suitable (Desert / Heavy Coastal Zone)",
            "description": "GPS matching, but location is Jaisalmer, Rajasthan (Zone 14 - Hyper-arid desert not recommended for maize). Shows Area Alert but allows existing stalk diagnosis.",
            "state": "Rajasthan",
            "district": "Jaisalmer",
            "taluka": "Pokhran",
            "village": "Desert Area",
            "entered_lat": 26.9157,
            "entered_lon": 70.9083,
            "gps_lat": 26.9160,
            "gps_lon": 70.9085,  # MATCH
            "season": "KHARIF",
            "sowing_date": "2026-07-01",
            "expected_outcome": "RED_AREA_NOT_SUITABLE alert"
        },
        {
            "case_id": "CASE_D",
            "title": "Case D: GPS Location Mismatch",
            "description": "Farmer entered farm in Begusarai (Bihar), but current GPS is detected 45km away in Patna. Triggers prominent Mismatch Alert with 4 action buttons.",
            "state": "Bihar",
            "district": "Begusarai",
            "taluka": "Barauni",
            "village": "Garhara",
            "entered_lat": 25.4182,
            "entered_lon": 86.1272,
            "gps_lat": 25.5941,
            "gps_lon": 85.1376,  # 102 km away (MISMATCH)
            "season": "RABI",
            "sowing_date": "2026-11-05",
            "expected_outcome": "LOCATION_MISMATCH alert with 4 action buttons"
        },
        {
            "case_id": "CASE_E",
            "title": "Case E: Invalid Crop Photo (Not Maize)",
            "description": "Location & time suitable, but uploaded image is a Tomato / Weed / Non-Maize plant. Rejects stalk height and disease inference.",
            "state": "Karnataka",
            "district": "Davangere",
            "taluka": "Harihar",
            "village": "Guttur",
            "entered_lat": 14.4644,
            "entered_lon": 75.9218,
            "gps_lat": 14.4645,
            "gps_lon": 75.9220,  # MATCH
            "season": "KHARIF",
            "sowing_date": "2026-06-10",
            "expected_outcome": "Invalid Crop Photograph Alert - Blocks Maize Predictions"
        }
    ]

    return {
        "states": states_list,
        "districts": districts_list,
        "zones": AGRO_CLIMATIC_ZONES,
        "case_presets": case_presets
    }
