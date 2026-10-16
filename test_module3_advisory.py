import asyncio
import sys
import os

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas import (
    Module3InputContract,
    Module2DiagnosticSignals,
    EnvironmentalContext,
    FarmGroundTruth,
    PriorityTierEnum,
    StressHypothesisEnum,
    RecommendationStatusEnum
)
from app.services.advisory_service import AdvisoryService

async def run_all_tests():
    print("=========================================================================")
    print("   RUNNING MODULE 3 AUTHORITATIVE ACCEPTANCE TEST SUITE (TC-01 TO TC-08)")
    print("=========================================================================\n")

    passed_count = 0
    total_tests = 8

    # -------------------------------------------------------------------------
    # TC-01: Stunted + Low Rainfall Weather Proxy (< 1 mm) + Healthy Disease
    # -------------------------------------------------------------------------
    tc01_input = Module3InputContract(
        diagnostics=Module2DiagnosticSignals(
            scan_id="tc01_scan",
            visual_week="Week 5",
            visual_confidence=0.88,
            calculated_das=32,
            measured_height_cm=35.0,
            expected_height_range_str="50–80 cm",
            height_status="BELOW_EXPECTED",
            detected_disease="Healthy",
            disease_confidence=0.95
        ),
        environment=EnvironmentalContext(
            rainfall_mm=0.2,
            temperature_c=29.0,
            humidity_percent=55,
            wind_speed_kmh=8.0,
            hours_until_rain=24.0,
            season="KHARIF",
            district="Panchmahal",
            agro_climatic_zone="Zone III"
        ),
        farm=FarmGroundTruth(
            farm_id="farm_tc01",
            uid="user_tc01",
            crop_type="Corn",
            variety="GAYMH-1",
            soil_type="Sandy Loam",
            farm_area_acres=2.0,
            sowing_date="2026-06-01"
        )
    )
    res_01 = await AdvisoryService.generate_farm_advisory(tc01_input)
    assert res_01.diagnostic.stress_hypothesis == StressHypothesisEnum.WATER_STRESS.value, f"TC-01 Fail: Expected WATER_STRESS, got {res_01.diagnostic.stress_hypothesis}"
    assert res_01.recommendation_status == RecommendationStatusEnum.RESTORE_WATER_AVAILABILITY, f"TC-01 Fail: Expected RESTORE_WATER_AVAILABILITY, got {res_01.recommendation_status}"
    assert res_01.fertilizer_advisory is None, "TC-01 Fail: Nitrogen fertilizer must be locked out during water stress!"
    assert res_01.safety_validation["lockout_nitrogen"] is True, "TC-01 Fail: Nitrogen lockout flag should be True"
    print("[PASS] TC-01 PASSED: Stunted growth + dry weather proxy correctly triggers RESTORE_WATER_AVAILABILITY with Nitrogen lockout.")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TC-02: High Confidence Fungal Rust (91%)
    # -------------------------------------------------------------------------
    tc02_input = Module3InputContract(
        diagnostics=Module2DiagnosticSignals(
            scan_id="tc02_scan",
            visual_week="Week 4",
            visual_confidence=0.90,
            calculated_das=25,
            measured_height_cm=55.0,
            expected_height_range_str="45–70 cm",
            height_status="WITHIN_EXPECTED",
            detected_disease="Corn Common Rust",
            disease_confidence=0.91
        ),
        environment=EnvironmentalContext(
            rainfall_mm=5.0,
            temperature_c=27.0,
            humidity_percent=70,
            wind_speed_kmh=6.0,
            hours_until_rain=24.0,
            season="KHARIF",
            district="Panchmahal",
            agro_climatic_zone="Zone III"
        ),
        farm=FarmGroundTruth(
            farm_id="farm_tc02",
            uid="user_tc02",
            crop_type="Corn",
            variety="GAYMH-1",
            soil_type="Goradu",
            farm_area_acres=1.0,
            sowing_date="2026-06-01"
        )
    )
    res_02 = await AdvisoryService.generate_farm_advisory(tc02_input)
    assert res_02.priority_tier == PriorityTierEnum.PROTECTION, f"TC-02 Fail: Expected PROTECTION, got {res_02.priority_tier}"
    assert res_02.pesticide_treatment is not None, "TC-02 Fail: Expected pesticide treatment plan from DB catalog"
    assert res_02.pesticide_treatment.product_name != "", "TC-02 Fail: Product name should be retrieved dynamically from DB"
    print(f"[PASS] TC-02 PASSED: High-confidence Rust (91%) retrieved protection treatment dynamically ({res_02.pesticide_treatment.product_name}).")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TC-03: Low Confidence Fungal Rust (62% < 75% threshold)
    # -------------------------------------------------------------------------
    tc03_input = Module3InputContract(
        diagnostics=Module2DiagnosticSignals(
            scan_id="tc03_scan",
            visual_week="Week 4",
            visual_confidence=0.90,
            calculated_das=25,
            measured_height_cm=55.0,
            expected_height_range_str="45–70 cm",
            height_status="WITHIN_EXPECTED",
            detected_disease="Corn Common Rust",
            disease_confidence=0.62
        ),
        environment=EnvironmentalContext(
            rainfall_mm=5.0,
            temperature_c=27.0,
            humidity_percent=70,
            wind_speed_kmh=6.0,
            hours_until_rain=24.0,
            season="KHARIF",
            district="Panchmahal",
            agro_climatic_zone="Zone III"
        ),
        farm=FarmGroundTruth(
            farm_id="farm_tc03",
            uid="user_tc03",
            crop_type="Corn",
            variety="GAYMH-1",
            soil_type="Goradu",
            farm_area_acres=1.0,
            sowing_date="2026-06-01"
        )
    )
    res_03 = await AdvisoryService.generate_farm_advisory(tc03_input)
    assert res_03.recommendation_status == RecommendationStatusEnum.PERFORM_FIELD_INSPECTION, f"TC-03 Fail: Expected PERFORM_FIELD_INSPECTION, got {res_03.recommendation_status}"
    assert res_03.pesticide_treatment is None, "TC-03 Fail: No toxic pesticides must be prescribed when confidence < 75%!"
    print("[PASS] TC-03 PASSED: Low-confidence disease (62%) locked out chemical spray and requested PERFORM_FIELD_INSPECTION.")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TC-04: Stunted + Normal Rainfall + No Chlorosis + Healthy Disease
    # -------------------------------------------------------------------------
    tc04_input = Module3InputContract(
        diagnostics=Module2DiagnosticSignals(
            scan_id="tc04_scan",
            visual_week="Week 5",
            visual_confidence=0.88,
            calculated_das=32,
            measured_height_cm=35.0,
            expected_height_range_str="50–80 cm",
            height_status="BELOW_EXPECTED",
            detected_disease="Healthy",
            disease_confidence=0.95,
            scouting_observations=[]
        ),
        environment=EnvironmentalContext(
            rainfall_mm=12.0,
            temperature_c=28.0,
            humidity_percent=68,
            wind_speed_kmh=7.0,
            hours_until_rain=24.0,
            season="KHARIF",
            district="Panchmahal",
            agro_climatic_zone="Zone III"
        ),
        farm=FarmGroundTruth(
            farm_id="farm_tc04",
            uid="user_tc04",
            crop_type="Corn",
            variety="GAYMH-1",
            soil_type="Sandy Loam",
            farm_area_acres=1.5,
            sowing_date="2026-06-01"
        )
    )
    res_04 = await AdvisoryService.generate_farm_advisory(tc04_input)
    assert res_04.recommendation_status == RecommendationStatusEnum.INSUFFICIENT_EVIDENCE, f"TC-04 Fail: Expected INSUFFICIENT_EVIDENCE, got {res_04.recommendation_status}"
    assert res_04.fertilizer_advisory is None, "TC-04 Fail: Must not prescribe chemical fertilizer on ambiguous stunting!"
    assert res_04.pesticide_treatment is None, "TC-04 Fail: Must not prescribe pesticide on ambiguous stunting!"
    print("[PASS] TC-04 PASSED: Ambiguous stunting safely returned INSUFFICIENT_EVIDENCE (Do Nothing Chemically).")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TC-05: Week 3 Healthy Phenological Maintenance
    # -------------------------------------------------------------------------
    tc05_input = Module3InputContract(
        diagnostics=Module2DiagnosticSignals(
            scan_id="tc05_scan",
            visual_week="Week 3",
            visual_confidence=0.92,
            calculated_das=18,
            measured_height_cm=40.0,
            expected_height_range_str="30–50 cm",
            height_status="WITHIN_EXPECTED",
            detected_disease="Healthy",
            disease_confidence=0.96
        ),
        environment=EnvironmentalContext(
            rainfall_mm=15.0,
            temperature_c=28.0,
            humidity_percent=70,
            wind_speed_kmh=5.0,
            hours_until_rain=24.0,
            season="KHARIF",
            district="Panchmahal",
            agro_climatic_zone="Zone III"
        ),
        farm=FarmGroundTruth(
            farm_id="farm_tc05",
            uid="user_tc05",
            crop_type="Corn",
            variety="GAYMH-1",
            soil_type="Goradu",
            farm_area_acres=1.0,
            sowing_date="2026-06-01"
        )
    )
    res_05 = await AdvisoryService.generate_farm_advisory(tc05_input)
    assert res_05.priority_tier == PriorityTierEnum.MAINTENANCE, f"TC-05 Fail: Expected MAINTENANCE, got {res_05.priority_tier}"
    assert res_05.fertilizer_advisory is not None, "TC-05 Fail: Expected routine split fertilizer recommendation"
    print("[PASS] TC-05 PASSED: Normal Week 3 crop generated MAINTENANCE split fertilizer advisory.")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TC-06: Farm Acreage Quantity Scaler (3.5 Acres)
    # -------------------------------------------------------------------------
    tc06_input = Module3InputContract(
        diagnostics=Module2DiagnosticSignals(
            scan_id="tc06_scan",
            visual_week="Week 4",
            visual_confidence=0.90,
            calculated_das=25,
            measured_height_cm=55.0,
            expected_height_range_str="45–70 cm",
            height_status="WITHIN_EXPECTED",
            detected_disease="Corn Common Rust",
            disease_confidence=0.91
        ),
        environment=EnvironmentalContext(
            rainfall_mm=5.0,
            temperature_c=27.0,
            humidity_percent=70,
            wind_speed_kmh=6.0,
            hours_until_rain=24.0,
            season="KHARIF",
            district="Panchmahal",
            agro_climatic_zone="Zone III"
        ),
        farm=FarmGroundTruth(
            farm_id="farm_tc06",
            uid="user_tc06",
            crop_type="Corn",
            variety="GAYMH-1",
            soil_type="Goradu",
            farm_area_acres=3.5,
            sowing_date="2026-06-01"
        )
    )
    res_06 = await AdvisoryService.generate_farm_advisory(tc06_input)
    # 200 ml/acre * 3.5 acres = 700.0 ml
    assert "700" in res_06.pesticide_treatment.total_quantity, f"TC-06 Fail: Expected 700 ml scaled for 3.5 acres, got {res_06.pesticide_treatment.total_quantity}"
    print(f"[PASS] TC-06 PASSED: Acreage scaler correctly calculated total batch quantity ({res_06.pesticide_treatment.total_quantity}) for 3.5 acres.")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TC-07: Rainfastness Safety Gate (Rain forecast in 1.5h vs 3.0h rainfastness)
    # -------------------------------------------------------------------------
    tc07_input = Module3InputContract(
        diagnostics=Module2DiagnosticSignals(
            scan_id="tc07_scan",
            visual_week="Week 4",
            visual_confidence=0.90,
            calculated_das=25,
            measured_height_cm=55.0,
            expected_height_range_str="45–70 cm",
            height_status="WITHIN_EXPECTED",
            detected_disease="Corn Common Rust",
            disease_confidence=0.91
        ),
        environment=EnvironmentalContext(
            rainfall_mm=5.0,
            temperature_c=27.0,
            humidity_percent=70,
            wind_speed_kmh=6.0,
            hours_until_rain=1.5,  # Rain sooner than 3.0h rainfastness!
            season="KHARIF",
            district="Panchmahal",
            agro_climatic_zone="Zone III"
        ),
        farm=FarmGroundTruth(
            farm_id="farm_tc07",
            uid="user_tc07",
            crop_type="Corn",
            variety="GAYMH-1",
            soil_type="Goradu",
            farm_area_acres=1.0,
            sowing_date="2026-06-01"
        )
    )
    res_07 = await AdvisoryService.generate_farm_advisory(tc07_input)
    assert res_07.recommendation_status == RecommendationStatusEnum.TREATMENT_NOT_AUTHORIZED, f"TC-07 Fail: Expected TREATMENT_NOT_AUTHORIZED due to rain washout risk, got {res_07.recommendation_status}"
    assert res_07.pesticide_treatment is None, "TC-07 Fail: Pesticide treatment must be held back when rain washout is imminent!"
    assert res_07.safety_validation["weather_safe_to_spray"] is False, "TC-07 Fail: weather_safe_to_spray should be False"
    print("[PASS] TC-07 PASSED: Rainfastness safety gate held back chemical spray due to imminent rainfall.")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TC-08: Disease High Confidence (92%), but Unknown Disease in DB Catalog
    # -------------------------------------------------------------------------
    tc08_input = Module3InputContract(
        diagnostics=Module2DiagnosticSignals(
            scan_id="tc08_scan",
            visual_week="Week 4",
            visual_confidence=0.90,
            calculated_das=25,
            measured_height_cm=55.0,
            expected_height_range_str="45–70 cm",
            height_status="WITHIN_EXPECTED",
            detected_disease="Unregistered Exotic Fungi",
            disease_confidence=0.92
        ),
        environment=EnvironmentalContext(
            rainfall_mm=5.0,
            temperature_c=27.0,
            humidity_percent=70,
            wind_speed_kmh=6.0,
            hours_until_rain=24.0,
            season="KHARIF",
            district="Panchmahal",
            agro_climatic_zone="Zone III"
        ),
        farm=FarmGroundTruth(
            farm_id="farm_tc08",
            uid="user_tc08",
            crop_type="Corn",
            variety="GAYMH-1",
            soil_type="Goradu",
            farm_area_acres=1.0,
            sowing_date="2026-06-01"
        )
    )
    res_08 = await AdvisoryService.generate_farm_advisory(tc08_input)
    assert res_08.recommendation_status == RecommendationStatusEnum.TREATMENT_NOT_AUTHORIZED, f"TC-08 Fail: Expected TREATMENT_NOT_AUTHORIZED when DB catalog has no registered chemical, got {res_08.recommendation_status}"
    assert res_08.pesticide_treatment is None, "TC-08 Fail: System must not invent unvalidated chemicals"
    print("[PASS] TC-08 PASSED: Confirmed that Disease Detected != Treatment Authorized when DB catalog lacks registered chemicals.")
    passed_count += 1

    print("\n=========================================================================")
    print(f" [SUCCESS]: ALL {passed_count}/{total_tests} MODULE 3 ACCEPTANCE TESTS PASSED!")
    print("=========================================================================")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
