import math
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, Union

from ..data.maize_suitability_data import (
    AGRO_CLIMATIC_ZONES,
    DISTRICT_MAIZE_DATABASE,
    TALUKA_VILLAGE_OVERRIDES,
    STATE_MAIZE_DEFAULTS,
    NATIONAL_FALLBACK_MAIZE
)

logger = logging.getLogger("agroguard.suitability_service")

class SuitabilityService:
    """
    Dedicated Agronomic Suitability Engine for Maize Cultivation.
    Implements 2-tier location verification and time-specific crop evaluation.
    """

    @staticmethod
    def calculate_haversine_distance_meters(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculates great-circle distance between two GPS coordinates in meters.
        """
        R = 6371000.0  # Earth's radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 1)

    @classmethod
    def checkLocationVerification(
        cls,
        entered_lat: Optional[float],
        entered_lon: Optional[float],
        gps_lat: Optional[float],
        gps_lon: Optional[float],
        threshold_meters: float = 1000.0
    ) -> Dict[str, Any]:
        """
        Question 1: Is the farmer actually at the location they entered?
        Compares entered farm coordinates with detected GPS navigation location.
        """
        now_ts = datetime.utcnow().isoformat()

        # If coordinates are missing, return unverified state
        if entered_lat is None or entered_lon is None or gps_lat is None or gps_lon is None:
            return {
                "status": "UNVERIFIED",
                "distance_meters": None,
                "threshold_meters": threshold_meters,
                "entered_coordinates": {"lat": entered_lat, "lon": entered_lon},
                "gps_coordinates": {"lat": gps_lat, "lon": gps_lon},
                "headline": "⚠ GPS Coordinates Incomplete",
                "message": "GPS coordinates could not be acquired or farm coordinates are missing.",
                "timestamp": now_ts
            }

        dist = cls.calculate_haversine_distance_meters(entered_lat, entered_lon, gps_lat, gps_lon)

        if dist <= threshold_meters:
            return {
                "status": "VERIFIED",
                "distance_meters": dist,
                "threshold_meters": threshold_meters,
                "entered_coordinates": {"lat": entered_lat, "lon": entered_lon},
                "gps_coordinates": {"lat": gps_lat, "lon": gps_lon},
                "headline": "✓ Location Verified",
                "message": f"Your current location matches the farm location you entered (distance: {int(dist)} m).",
                "timestamp": now_ts
            }
        else:
            return {
                "status": "MISMATCH",
                "distance_meters": dist,
                "threshold_meters": threshold_meters,
                "entered_coordinates": {"lat": entered_lat, "lon": entered_lon},
                "gps_coordinates": {"lat": gps_lat, "lon": gps_lon},
                "headline": "⚠ LOCATION MISMATCH",
                "message": f"Your current GPS location does not appear to match the farm location you entered (distance deviation: {dist / 1000.0:.2f} km). Please verify your farm location.",
                "actions": [
                    "Recheck Location",
                    "Use Current Location",
                    "Edit Farm Location",
                    "Continue With Warning"
                ],
                "timestamp": now_ts
            }

    @classmethod
    def checkAreaSuitability(
        cls,
        state: Optional[str] = None,
        district: Optional[str] = None,
        taluka: Optional[str] = None,
        village: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Question 2: Is maize suitable for that geographical area?
        Evaluates location using Priority:
        1. Village/Taluka -> 2. District -> 3. Agro-climatic Zone -> 4. State -> 5. National
        """
        state_clean = (state or "").strip().title()
        district_clean = (district or "").strip().title()
        taluka_clean = (taluka or "").strip().title()
        village_clean = (village or "").strip().title()

        # Priority 1: Taluka / Village match
        taluka_key = f"{state_clean.lower()}_{district_clean.lower()}_{taluka_clean.lower()}"
        if taluka_key in TALUKA_VILLAGE_OVERRIDES:
            t_data = TALUKA_VILLAGE_OVERRIDES[taluka_key]
            # Lookup parent district for season windows
            d_key = f"{state_clean.lower()}_{district_clean.lower()}"
            parent_d = DISTRICT_MAIZE_DATABASE.get(d_key, {})
            zone_key = parent_d.get("zone_key", "ZONE_13")
            zone_info = AGRO_CLIMATIC_ZONES.get(zone_key, {})

            return {
                "status": "SUITABLE" if t_data.get("is_suitable", True) else "NOT_RECOMMENDED",
                "data_level": "TALUKA",
                "matched_location": f"{taluka_clean}, {district_clean}, {state_clean}",
                "agro_climatic_zone": {
                    "code": zone_key,
                    "name": zone_info.get("name", "Regional Zone"),
                    "description": zone_info.get("description", ""),
                    "optimal_ph": zone_info.get("optimal_ph", "6.0 - 7.5"),
                    "soil_suitability": zone_info.get("soil_suitability", "Loamy soil")
                },
                "soil_suitability": parent_d.get("soil_type", zone_info.get("soil_suitability", "Well-drained Loam")),
                "recommended_varieties": t_data.get("recommended_varieties", parent_d.get("varieties", zone_info.get("default_varieties", []))),
                "special_notes": t_data.get("special_recommendation", ""),
                "unsuitable_reason": t_data.get("unsuitable_reason", ""),
                "seasons": parent_d.get("seasons", {})
            }

        # Priority 2: District match
        district_key = f"{state_clean.lower()}_{district_clean.lower()}"
        if district_key in DISTRICT_MAIZE_DATABASE:
            d_data = DISTRICT_MAIZE_DATABASE[district_key]
            zone_key = d_data.get("zone_key", "ZONE_13")
            zone_info = AGRO_CLIMATIC_ZONES.get(zone_key, {})

            return {
                "status": "SUITABLE" if d_data.get("is_suitable", True) else "NOT_RECOMMENDED",
                "data_level": "DISTRICT",
                "matched_location": f"{district_clean}, {state_clean}",
                "agro_climatic_zone": {
                    "code": zone_key,
                    "name": zone_info.get("name", "Regional Zone"),
                    "description": zone_info.get("description", ""),
                    "optimal_ph": zone_info.get("optimal_ph", "6.0 - 7.5"),
                    "soil_suitability": zone_info.get("soil_suitability", "Loamy soil")
                },
                "soil_suitability": d_data.get("soil_type", zone_info.get("soil_suitability", "Well-drained Loam")),
                "recommended_varieties": zone_info.get("default_varieties", []),
                "special_notes": "",
                "unsuitable_reason": d_data.get("unsuitable_reason", ""),
                "seasons": d_data.get("seasons", {})
            }

        # Priority 3 & 4: State level baseline & Agro-Climatic Zone
        if state_clean in STATE_MAIZE_DEFAULTS:
            s_data = STATE_MAIZE_DEFAULTS[state_clean]
            zone_key = s_data.get("zone_key", "ZONE_13")
            zone_info = AGRO_CLIMATIC_ZONES.get(zone_key, {})

            # Construct season windows from defaults
            seasons_dict = {}
            for s_name, (s_start, s_end) in s_data.get("default_sowing", {}).items():
                seasons_dict[s_name] = {
                    "recommended_start": s_start,
                    "recommended_end": s_end,
                    "peak_period": f"Standard {s_name} window",
                    "varieties": s_data.get("varieties", []),
                    "notes": f"State-level agro-climatic baseline for {state_clean}."
                }

            return {
                "status": "SUITABLE" if s_data.get("is_suitable", True) else "NOT_RECOMMENDED",
                "data_level": "STATE",
                "matched_location": state_clean,
                "agro_climatic_zone": {
                    "code": zone_key,
                    "name": zone_info.get("name", "Agro-Climatic Zone"),
                    "description": zone_info.get("description", ""),
                    "optimal_ph": zone_info.get("optimal_ph", "5.8 - 7.5"),
                    "soil_suitability": zone_info.get("soil_suitability", "Alluvial / Loamy")
                },
                "soil_suitability": s_data.get("soil_type", "Loamy Sand to Clay Loam"),
                "recommended_varieties": s_data.get("varieties", zone_info.get("default_varieties", [])),
                "special_notes": f"State-level recommendation for {state_clean}.",
                "unsuitable_reason": s_data.get("unsuitable_reason", ""),
                "seasons": seasons_dict
            }

        # Priority 5: National Fallback
        nat_zone = {
            "code": "ZONE_NATIONAL",
            "name": "All-India Average Agro-Climatic Baseline",
            "description": "General sub-tropical agricultural zone with seasonal monsoon rains.",
            "optimal_ph": "5.8 - 7.5",
            "soil_suitability": NATIONAL_FALLBACK_MAIZE["optimal_soil"]
        }
        return {
            "status": "SUITABLE",
            "data_level": "NATIONAL",
            "matched_location": state_clean or "All-India",
            "agro_climatic_zone": nat_zone,
            "soil_suitability": NATIONAL_FALLBACK_MAIZE["optimal_soil"],
            "recommended_varieties": ["HQPM-1", "Bio-9681", "Ganga-11", "PAC-751"],
            "special_notes": "National baseline recommendation used. District-level record not found.",
            "unsuitable_reason": "",
            "seasons": NATIONAL_FALLBACK_MAIZE["seasons"]
        }

    @classmethod
    def checkSeasonSuitability(
        cls,
        area_result: Dict[str, Any],
        season: Optional[str] = "KHARIF"
    ) -> Dict[str, Any]:
        """
        Checks whether the selected season is supported for Maize in this location.
        """
        season_clean = (season or "KHARIF").strip().upper()
        available_seasons = area_result.get("seasons", {})

        if area_result.get("status") == "NOT_RECOMMENDED":
            return {
                "status": "NOT_RECOMMENDED",
                "season": season_clean,
                "supported_seasons": list(available_seasons.keys()),
                "message": f"Maize cultivation is not recommended for this area during any season."
            }

        if season_clean in available_seasons:
            return {
                "status": "SUITABLE",
                "season": season_clean,
                "supported_seasons": list(available_seasons.keys()),
                "message": f"{season_clean} is an established cultivation season for Maize in this region."
            }
        else:
            supported_str = ", ".join(available_seasons.keys()) if available_seasons else "None"
            return {
                "status": "NOT_RECOMMENDED",
                "season": season_clean,
                "supported_seasons": list(available_seasons.keys()),
                "message": f"{season_clean} season is not recommended for Maize in this location. Supported seasons: {supported_str}."
            }

    @classmethod
    def checkSowingDateSuitability(
        cls,
        area_result: Dict[str, Any],
        season: str,
        sowing_date: Union[str, date, datetime, None]
    ) -> Dict[str, Any]:
        """
        Question 3: Is this the appropriate season and sowing period for maize at that location?
        Compares farmer's sowing date against the regional sowing window for that season.
        """
        season_clean = (season or "KHARIF").strip().upper()
        available_seasons = area_result.get("seasons", {})
        season_data = available_seasons.get(season_clean)

        # Fallback to national window if season is not in district data
        if not season_data:
            season_data = NATIONAL_FALLBACK_MAIZE["seasons"].get(season_clean, {
                "recommended_start": "06-15",
                "recommended_end": "07-15",
                "peak_period": "June 25 - July 05"
            })

        # Parse farmer sowing date
        farmer_dt = None
        if isinstance(sowing_date, datetime):
            farmer_dt = sowing_date.date()
        elif isinstance(sowing_date, date):
            farmer_dt = sowing_date
        elif isinstance(sowing_date, str) and sowing_date.strip():
            try:
                farmer_dt = datetime.strptime(sowing_date.strip()[:10], "%Y-%m-%d").date()
            except ValueError:
                try:
                    farmer_dt = datetime.strptime(sowing_date.strip()[:10], "%d-%m-%Y").date()
                except ValueError:
                    farmer_dt = None

        # If no date provided, default to current date
        if farmer_dt is None:
            farmer_dt = date.today()

        rec_start_mm_dd = season_data.get("recommended_start", "06-15")
        rec_end_mm_dd = season_data.get("recommended_end", "07-15")
        peak_period = season_data.get("peak_period", "Mid-season")

        start_month, start_day = map(int, rec_start_mm_dd.split("-"))
        end_month, end_day = map(int, rec_end_mm_dd.split("-"))

        # Build full date bounds using farmer date's year
        year = farmer_dt.year
        rec_start_date = date(year, start_month, start_day)
        
        # Handle wrap around if end month is before start month (e.g. Rabi Oct to Jan)
        if end_month < start_month:
            if farmer_dt.month >= start_month:
                rec_end_date = date(year + 1, end_month, end_day)
            else:
                rec_start_date = date(year - 1, start_month, start_day)
                rec_end_date = date(year, end_month, end_day)
        else:
            rec_end_date = date(year, end_month, end_day)

        # Check if farmer date is within window
        farmer_date_str = farmer_dt.strftime("%Y-%m-%d")
        rec_start_str = rec_start_date.strftime("%Y-%m-%d")
        rec_end_str = rec_end_date.strftime("%Y-%m-%d")

        if rec_start_date <= farmer_dt <= rec_end_date:
            return {
                "status": "SUITABLE",
                "farmer_date": farmer_date_str,
                "recommended_start": rec_start_str,
                "recommended_end": rec_end_str,
                "peak_period": peak_period,
                "difference_days": 0,
                "season": season_clean,
                "message": f"Farmer sowing date ({farmer_date_str}) is within the recommended period ({rec_start_str} to {rec_end_str})."
            }
        elif farmer_dt < rec_start_date:
            diff_days = (rec_start_date - farmer_dt).days
            return {
                "status": "NOT_RECOMMENDED",
                "sub_status": "EARLY",
                "farmer_date": farmer_date_str,
                "recommended_start": rec_start_str,
                "recommended_end": rec_end_str,
                "peak_period": peak_period,
                "difference_days": diff_days,
                "season": season_clean,
                "message": f"Sowing date ({farmer_date_str}) is {diff_days} days earlier than recommended start ({rec_start_str}). Risk of cold stress or pre-monsoon moisture deficit."
            }
        else:
            diff_days = (farmer_dt - rec_end_date).days
            return {
                "status": "NOT_RECOMMENDED",
                "sub_status": "LATE",
                "farmer_date": farmer_date_str,
                "recommended_start": rec_start_str,
                "recommended_end": rec_end_str,
                "peak_period": peak_period,
                "difference_days": diff_days,
                "season": season_clean,
                "message": f"Maize is cultivated in this area, but the entered sowing date ({farmer_date_str}) is {diff_days} days past the recommended sowing period ({rec_start_str} to {rec_end_str}) for this location and season."
            }

    @classmethod
    def generateSuitabilityAlert(
        cls,
        gps_res: Dict[str, Any],
        area_res: Dict[str, Any],
        season_res: Dict[str, Any],
        sowing_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes the 4 distinct evaluation steps into the unified decision schema.
        Handles statuses:
        - GREEN — SUITABLE
        - YELLOW — TIME OUTSIDE RECOMMENDED PERIOD
        - RED — AREA NOT SUITABLE
        - RED — AREA + TIME NOT SUITABLE
        """
        area_ok = (area_res.get("status") == "SUITABLE")
        season_ok = (season_res.get("status") == "SUITABLE")
        sowing_ok = (sowing_res.get("status") == "SUITABLE")

        # 1. Decision Calculation
        if area_ok and season_ok and sowing_ok:
            decision_code = "GREEN_SUITABLE"
            overall_status = "PASS"
            headline = "✓ MAIZE IS SUITABLE FOR THIS LOCATION AND TIME"
            detail = "Your selected location and sowing period are suitable for maize cultivation."
            badge_color = "#10B981" # Green
        elif area_ok and season_ok and not sowing_ok:
            decision_code = "YELLOW_TIME_NOT_IDEAL"
            overall_status = "WARNING"
            headline = "⚠ SOWING TIME IS NOT IDEAL"
            diff = sowing_res.get("difference_days", 0)
            detail = f"Maize is cultivated in this area, but the entered sowing date is {diff} days outside the recommended sowing period ({sowing_res.get('recommended_start')} – {sowing_res.get('recommended_end')}) for this location and season."
            badge_color = "#F59E0B" # Yellow
        elif not area_ok and sowing_ok:
            decision_code = "RED_AREA_NOT_SUITABLE"
            overall_status = "FAIL"
            headline = "❌ AREA NOT RECOMMENDED FOR MAIZE"
            reason = area_res.get("unsuitable_reason") or "Agro-climatic and soil parameters in this geographical zone do not support standard maize cultivation."
            detail = f"According to the available agricultural data, maize is not recommended for this location. ({reason})"
            badge_color = "#EF4444" # Red
        else: # not area_ok and not sowing_ok
            decision_code = "RED_AREA_AND_TIME_NOT_SUITABLE"
            overall_status = "FAIL"
            headline = "❌ LOCATION AND SOWING PERIOD ARE NOT SUITABLE"
            detail = "The selected location and sowing period do not match the recommended conditions for maize cultivation."
            badge_color = "#EF4444" # Red

        return {
            "gps_verification": {
                "status": gps_res.get("status", "UNVERIFIED"),
                "distance_meters": gps_res.get("distance_meters"),
                "entered_coordinates": gps_res.get("entered_coordinates"),
                "gps_coordinates": gps_res.get("gps_coordinates"),
                "headline": gps_res.get("headline"),
                "message": gps_res.get("message")
            },
            "crop": "MAIZE",
            "area_suitability": {
                "status": area_res.get("status", "UNKNOWN"),
                "data_level": area_res.get("data_level", "NATIONAL"),
                "matched_location": area_res.get("matched_location"),
                "agro_climatic_zone": area_res.get("agro_climatic_zone"),
                "soil_suitability": area_res.get("soil_suitability"),
                "recommended_varieties": area_res.get("recommended_varieties", []),
                "special_notes": area_res.get("special_notes"),
                "unsuitable_reason": area_res.get("unsuitable_reason")
            },
            "season_suitability": {
                "status": season_res.get("status", "UNKNOWN"),
                "season": season_res.get("season", "KHARIF"),
                "supported_seasons": season_res.get("supported_seasons", []),
                "message": season_res.get("message")
            },
            "sowing_period": {
                "status": sowing_res.get("status", "UNKNOWN"),
                "sub_status": sowing_res.get("sub_status"),
                "farmer_date": sowing_res.get("farmer_date"),
                "recommended_start": sowing_res.get("recommended_start"),
                "recommended_end": sowing_res.get("recommended_end"),
                "peak_period": sowing_res.get("peak_period"),
                "difference_days": sowing_res.get("difference_days", 0),
                "message": sowing_res.get("message")
            },
            "decision": {
                "code": decision_code,
                "overall_status": overall_status,
                "headline": headline,
                "detail": detail,
                "badge_color": badge_color
            }
        }

    @classmethod
    def evaluate_farm_suitability(
        cls,
        state: Optional[str] = None,
        district: Optional[str] = None,
        taluka: Optional[str] = None,
        village: Optional[str] = None,
        entered_lat: Optional[float] = None,
        entered_lon: Optional[float] = None,
        gps_lat: Optional[float] = None,
        gps_lon: Optional[float] = None,
        season: str = "KHARIF",
        sowing_date: Union[str, date, datetime, None] = None
    ) -> Dict[str, Any]:
        """
        Convenience end-to-end evaluation executing all 4 steps.
        """
        gps_res = cls.checkLocationVerification(entered_lat, entered_lon, gps_lat, gps_lon)
        area_res = cls.checkAreaSuitability(state, district, taluka, village)
        season_res = cls.checkSeasonSuitability(area_res, season)
        sowing_res = cls.checkSowingDateSuitability(area_res, season, sowing_date)

        return cls.generateSuitabilityAlert(gps_res, area_res, season_res, sowing_res)
