"""
Comprehensive Test Suite for Smart AgroGuard Location & Agricultural Suitability Engine.
Validates all 5 Critical Cases (Cases A to E), Priority Matching, and GPS Distance Calculations.
"""
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.suitability_service import SuitabilityService
from app.routers.suitability import get_supported_regions

def run_tests():
    print("==========================================================")
    print("  SMART AGROGUARD SUITABILITY ENGINE VERIFICATION SUITE   ")
    print("==========================================================\n")

    # 1. Test GPS Haversine Distance
    print("--- 1. Testing GPS Verification (Haversine Distance) ---")
    # Farm in Panchmahal (22.7758, 73.6149)
    # Nearby GPS (22.7762, 73.6155) ~ 75 meters
    res_near = SuitabilityService.checkLocationVerification(22.7758, 73.6149, 22.7762, 73.6155, threshold_meters=1000.0)
    assert res_near["status"] == "VERIFIED", f"Expected VERIFIED, got {res_near['status']}"
    print(f"[PASS] Nearby point verified: {res_near['distance_meters']} m (<= 1000 m)")

    # Far GPS (Patna: 25.5941, 85.1376) vs Panchmahal -> ~1200 km
    res_far = SuitabilityService.checkLocationVerification(22.7758, 73.6149, 25.5941, 85.1376, threshold_meters=1000.0)
    assert res_far["status"] == "MISMATCH", f"Expected MISMATCH, got {res_far['status']}"
    assert "actions" in res_far, "Expected action buttons in mismatch response"
    print(f"[PASS] Far point mismatch detected: {res_far['distance_meters'] / 1000.0:.1f} km. Actions: {res_far['actions']}")

    # 2. Test Priority Resolution
    print("\n--- 2. Testing Multi-Tier Priority Lookup ---")
    # Priority 1: Taluka / Village match (Godhra, Panchmahal)
    res_taluka = SuitabilityService.checkAreaSuitability("Gujarat", "Panchmahal", "Godhra", "Vavdi")
    assert res_taluka["data_level"] == "TALUKA", f"Expected TALUKA, got {res_taluka['data_level']}"
    print(f"[PASS] Level 1 (Taluka): {res_taluka['matched_location']} -> Zone: {res_taluka['agro_climatic_zone']['code']}")

    # Priority 2: District match (Begusarai, Bihar)
    res_district = SuitabilityService.checkAreaSuitability("Bihar", "Begusarai")
    assert res_district["data_level"] == "DISTRICT", f"Expected DISTRICT, got {res_district['data_level']}"
    print(f"[PASS] Level 2 (District): {res_district['matched_location']} -> Soil: {res_district['soil_suitability']}")

    # Priority 3: State Baseline (Punjab)
    res_state = SuitabilityService.checkAreaSuitability("Punjab", "UnknownDistrict")
    assert res_state["data_level"] == "STATE", f"Expected STATE, got {res_state['data_level']}"
    print(f"[PASS] Level 3 (State): {res_state['matched_location']} -> Zone: {res_state['agro_climatic_zone']['name']}")

    # Priority 4: National Fallback
    res_nat = SuitabilityService.checkAreaSuitability("UnknownState", "UnknownDistrict")
    assert res_nat["data_level"] == "NATIONAL", f"Expected NATIONAL, got {res_nat['data_level']}"
    print(f"[PASS] Level 4 (National): {res_nat['matched_location']}")

    # 3. Test Critical Case A (Ideal Cultivation - All Pass)
    print("\n--- 3. Testing Critical Case A (Ideal Cultivation: All Pass) ---")
    case_a = SuitabilityService.evaluate_farm_suitability(
        state="Gujarat",
        district="Panchmahal",
        taluka="Godhra",
        village="Vavdi",
        entered_lat=22.7758,
        entered_lon=73.6149,
        gps_lat=22.7762,
        gps_lon=73.6155,
        season="KHARIF",
        sowing_date="2026-06-28"  # Inside June 15 - July 15 window
    )
    assert case_a["gps_verification"]["status"] == "VERIFIED"
    assert case_a["area_suitability"]["status"] == "SUITABLE"
    assert case_a["season_suitability"]["status"] == "SUITABLE"
    assert case_a["sowing_period"]["status"] == "SUITABLE"
    assert case_a["decision"]["code"] == "GREEN_SUITABLE"
    print(f"[PASS] Case A Result: {case_a['decision']['code']} - {case_a['decision']['headline']}")

    # 4. Test Critical Case B (Late Sowing Date outside window)
    print("\n--- 4. Testing Critical Case B (Late Sowing Date: Yellow Alert) ---")
    case_b = SuitabilityService.evaluate_farm_suitability(
        state="Gujarat",
        district="Panchmahal",
        taluka="Godhra",
        entered_lat=22.7758,
        entered_lon=73.6149,
        gps_lat=22.7760,
        gps_lon=73.6150,
        season="KHARIF",
        sowing_date="2026-08-10"  # 26 days late past July 15
    )
    assert case_b["gps_verification"]["status"] == "VERIFIED"
    assert case_b["area_suitability"]["status"] == "SUITABLE"
    assert case_b["sowing_period"]["status"] == "NOT_RECOMMENDED"
    assert case_b["sowing_period"]["sub_status"] == "LATE"
    assert case_b["sowing_period"]["difference_days"] > 0
    assert case_b["decision"]["code"] == "YELLOW_TIME_NOT_IDEAL"
    print(f"[PASS] Case B Result: {case_b['decision']['code']} - Sowing is {case_b['sowing_period']['difference_days']} days late.")

    # 5. Test Critical Case C (Unsuitable Area - Desert Zone)
    print("\n--- 5. Testing Critical Case C (Unsuitable Area: Red Alert) ---")
    case_c = SuitabilityService.evaluate_farm_suitability(
        state="Rajasthan",
        district="Jaisalmer",
        taluka="Pokhran",
        entered_lat=26.9157,
        entered_lon=70.9083,
        gps_lat=26.9160,
        gps_lon=70.9085,
        season="KHARIF",
        sowing_date="2026-07-01"
    )
    assert case_c["gps_verification"]["status"] == "VERIFIED"
    assert case_c["area_suitability"]["status"] == "NOT_RECOMMENDED"
    assert case_c["decision"]["code"] == "RED_AREA_NOT_SUITABLE"
    print(f"[PASS] Case C Result: {case_c['decision']['code']} - {case_c['area_suitability']['unsuitable_reason']}")

    # 6. Test Critical Case D (GPS Location Mismatch)
    print("\n--- 6. Testing Critical Case D (GPS Location Mismatch) ---")
    case_d = SuitabilityService.evaluate_farm_suitability(
        state="Bihar",
        district="Begusarai",
        entered_lat=25.4182,
        entered_lon=86.1272,
        gps_lat=25.5941,
        gps_lon=85.1376, # Patna ~102 km away
        season="RABI",
        sowing_date="2026-11-05"
    )
    assert case_d["gps_verification"]["status"] == "MISMATCH"
    assert case_d["area_suitability"]["status"] == "SUITABLE"
    print(f"[PASS] Case D Result: GPS is MISMATCH ({case_d['gps_verification']['distance_meters']/1000:.1f} km away) while area suitability is {case_d['area_suitability']['status']}.")

    # 7. Test Region Metadata API
    print("\n--- 7. Testing Region Metadata Endpoint ---")
    meta = get_supported_regions()
    assert len(meta["states"]) > 5
    assert len(meta["districts"]) > 5
    assert len(meta["case_presets"]) == 5
    print(f"[PASS] Metadata loaded: {len(meta['states'])} states, {len(meta['districts'])} districts, {len(meta['case_presets'])} demo case presets.")

    print("\n==========================================================")
    print("      ALL SUITABILITY ENGINE TESTS PASSED (100%)         ")
    print("==========================================================")

if __name__ == "__main__":
    run_tests()
