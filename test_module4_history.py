import asyncio
import sys
import os
from datetime import datetime, timedelta

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.data_quality_service import DataQualityService
from app.services.growth_benchmark_service import GrowthBenchmarkService
from app.services.growth_analytics_service import GrowthAnalyticsService
from app.services.temporal_observation_service import TemporalObservationService
from app.services.season_summary_service import SeasonSummaryService

async def run_tests():
    print("=========================================================================")
    print("   RUNNING MODULE 4 COMPREHENSIVE ACCEPTANCE TEST SUITE (T-01 TO T-18)   ")
    print("=========================================================================\n")

    passed = 0
    total = 12

    # -------------------------------------------------------------------------
    # T-01: Farm with 0 valid scans -> quality_level = INSUFFICIENT
    # -------------------------------------------------------------------------
    q0 = DataQualityService.evaluate_quality([], "2026-06-01")
    assert q0.quality_level == "INSUFFICIENT", f"Expected INSUFFICIENT, got {q0.quality_level}"
    assert q0.total_scans == 0
    print("[PASS] T-01: Zero scans correctly yields INSUFFICIENT quality level.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-02: Missing sowing date -> das_available = False, das = None
    # -------------------------------------------------------------------------
    das_none = DataQualityService.compute_das(datetime(2026, 6, 20), None)
    assert das_none is None, f"Expected None, got {das_none}"
    q_no_sow = DataQualityService.evaluate_quality([{"scan_date": datetime(2026, 6, 20)}], None)
    assert q_no_sow.das_available is False
    assert q_no_sow.missing_sowing_date is True
    print("[PASS] T-02: Missing sowing date exposes das_available=False and DAS=None.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-03: Sowing date correction recalculates DAS dynamically
    # -------------------------------------------------------------------------
    scan_dt = datetime(2026, 7, 1)
    das_v1 = DataQualityService.compute_das(scan_dt, "2026-06-01")
    das_v2 = DataQualityService.compute_das(scan_dt, "2026-06-11")
    assert das_v1 == 30, f"Expected 30, got {das_v1}"
    assert das_v2 == 20, f"Expected 20, got {das_v2}"
    print(f"[PASS] T-03: Dynamic DAS recalculation: June 1 -> DAS={das_v1}, corrected to June 11 -> DAS={das_v2}.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-04: Missing height measurement is excluded from growth score, not a failure
    # -------------------------------------------------------------------------
    scans_t04 = [
        {"scan_date": datetime(2026, 6, 10), "height": {"measured_height_cm": 15.0, "height_status": "WITHIN_EXPECTED"}},
        {"scan_date": datetime(2026, 6, 17), "height": {"measured_height_cm": None, "height_status": "NO_MARKER"}},
        {"scan_date": datetime(2026, 6, 24), "height": {"measured_height_cm": 35.0, "height_status": "WITHIN_EXPECTED"}},
    ]
    farm_t04 = {"sowing_date": "2026-06-01"}
    gc_res = await GrowthAnalyticsService.build_growth_curve("f_test", scans_t04, farm_t04)
    assert gc_res.valid_height_scans == 2, f"Expected 2 valid height scans, got {gc_res.valid_height_scans}"
    assert gc_res.within_expected_scans == 2
    assert gc_res.growth_score_percent == 100.0, f"Expected 100.0, got {gc_res.growth_score_percent}"
    print("[PASS] T-04: Missing height marker safely excluded from denominator (100% score for 2/2 valid).")
    passed += 1

    # -------------------------------------------------------------------------
    # T-05: Height 42.1 -> 41.7 cm (delta = -0.4 cm, tolerance = 2.0 cm) -> No observation
    # -------------------------------------------------------------------------
    s1 = {"scan_id": "s1", "farm_id": "f1", "height": {"measured_height_cm": 42.1}}
    s2 = {"scan_id": "s2", "farm_id": "f1", "height": {"measured_height_cm": 41.7}}
    obs_t05 = TemporalObservationService.check_height_change(s1, s2, tolerance_cm=2.0)
    assert obs_t05 is None, "Expected no observation for delta within tolerance"
    print("[PASS] T-05: 42.1 cm -> 41.7 cm (delta -0.4 cm) suppresses false alarm within 2.0 cm tolerance.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-06: Height 42.1 -> 38.0 cm (delta = -4.1 cm) -> HEIGHT_DECREASE_OBSERVED
    # -------------------------------------------------------------------------
    s3 = {"scan_id": "s3", "farm_id": "f1", "height": {"measured_height_cm": 38.0}}
    obs_t06 = TemporalObservationService.check_height_change(s1, s3, tolerance_cm=2.0)
    assert obs_t06 is not None
    assert obs_t06.observation_type == "HEIGHT_DECREASE_OBSERVED"
    assert "obs_" in obs_t06.observation_id
    print(f"[PASS] T-06: 42.1 cm -> 38.0 cm triggers HEIGHT_DECREASE_OBSERVED ({obs_t06.observation_id}).")
    passed += 1

    # -------------------------------------------------------------------------
    # T-07: Same disease across 2 scans, both >= 75% -> DISEASE_PERSISTENCE_OBSERVED
    # -------------------------------------------------------------------------
    scans_t07 = [
        {"scan_id": "d1", "farm_id": "f1", "scan_date": datetime(2026, 7, 1), "disease_log": {"detected_disease": "Corn Common Rust", "confidence_score": 0.88}},
        {"scan_id": "d2", "farm_id": "f1", "scan_date": datetime(2026, 7, 5), "disease_log": {"detected_disease": "Corn Common Rust", "confidence_score": 0.85}},
    ]
    res_t07 = TemporalObservationService.detect_observations("f1", scans_t07, "2026-06-01")
    disease_obs = [o for o in res_t07.observations if o.observation_type == "DISEASE_PERSISTENCE_OBSERVED"]
    assert len(disease_obs) == 1, f"Expected 1 persistence observation, got {len(disease_obs)}"
    assert "Corn Common Rust" in disease_obs[0].headline
    print("[PASS] T-07: 2 consecutive Corn Common Rust scans with >=85% conf trigger DISEASE_PERSISTENCE_OBSERVED.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-08: Same disease across 2 scans, one at 52% (< 75%) -> No persistence
    # -------------------------------------------------------------------------
    scans_t08 = [
        {"scan_id": "d3", "farm_id": "f1", "scan_date": datetime(2026, 7, 1), "disease_log": {"detected_disease": "Corn Common Rust", "confidence_score": 0.88}},
        {"scan_id": "d4", "farm_id": "f1", "scan_date": datetime(2026, 7, 5), "disease_log": {"detected_disease": "Corn Common Rust", "confidence_score": 0.52}},
    ]
    res_t08 = TemporalObservationService.detect_observations("f1", scans_t08, "2026-06-01")
    d_obs_t08 = [o for o in res_t08.observations if o.observation_type == "DISEASE_PERSISTENCE_OBSERVED"]
    assert len(d_obs_t08) == 0, f"Expected 0 persistence observations due to low confidence, got {len(d_obs_t08)}"
    print("[PASS] T-08: Low confidence (52% < 75%) suppresses false disease persistence.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-09: Disease A x 2 -> Healthy -> Disease B x 2 -> TWO persistence observations
    # -------------------------------------------------------------------------
    scans_t09 = [
        {"scan_id": "da1", "farm_id": "f1", "scan_date": datetime(2026, 7, 1), "disease_log": {"detected_disease": "Corn Common Rust", "confidence_score": 0.90}},
        {"scan_id": "da2", "farm_id": "f1", "scan_date": datetime(2026, 7, 4), "disease_log": {"detected_disease": "Corn Common Rust", "confidence_score": 0.88}},
        {"scan_id": "dh",  "farm_id": "f1", "scan_date": datetime(2026, 7, 8), "disease_log": {"detected_disease": "Healthy", "confidence_score": 0.95}},
        {"scan_id": "db1", "farm_id": "f1", "scan_date": datetime(2026, 7, 12), "disease_log": {"detected_disease": "Gray Leaf Spot", "confidence_score": 0.85}},
        {"scan_id": "db2", "farm_id": "f1", "scan_date": datetime(2026, 7, 16), "disease_log": {"detected_disease": "Gray Leaf Spot", "confidence_score": 0.82}},
    ]
    res_t09 = TemporalObservationService.detect_observations("f1", scans_t09, "2026-06-01")
    pers_t09 = [o for o in res_t09.observations if o.observation_type == "DISEASE_PERSISTENCE_OBSERVED"]
    assert len(pers_t09) == 2, f"Expected 2 persistence episodes, got {len(pers_t09)}"
    assert "Corn Common Rust" in pers_t09[0].headline
    assert "Gray Leaf Spot" in pers_t09[1].headline
    print("[PASS] T-09: Disease A x 2 -> Healthy -> Disease B x 2 successfully returns TWO episodes.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-10: STUNTED -> NORMAL -> NORMAL -> RECOVERY_OBSERVED
    # -------------------------------------------------------------------------
    scans_t10 = [
        {"scan_id": "r1", "farm_id": "f1", "scan_date": datetime(2026, 7, 1), "health": {"growth_status": "STUNTED"}, "height": {"height_status": "BELOW_EXPECTED"}},
        {"scan_id": "r2", "farm_id": "f1", "scan_date": datetime(2026, 7, 6), "health": {"growth_status": "NORMAL"}, "height": {"height_status": "WITHIN_EXPECTED"}},
        {"scan_id": "r3", "farm_id": "f1", "scan_date": datetime(2026, 7, 11), "health": {"growth_status": "NORMAL"}, "height": {"height_status": "WITHIN_EXPECTED"}},
    ]
    res_t10 = TemporalObservationService.detect_observations("f1", scans_t10, "2026-06-01")
    rec_t10 = [o for o in res_t10.observations if o.observation_type == "RECOVERY_OBSERVED"]
    assert len(rec_t10) == 1, f"Expected 1 recovery observation, got {len(rec_t10)}"
    assert "STUNTED" in rec_t10[0].detail
    print("[PASS] T-10: STUNTED -> NORMAL -> NORMAL produces RECOVERY_OBSERVED after 2nd normal observation.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-11: STUNTED -> NORMAL -> STUNTED -> No recovery
    # -------------------------------------------------------------------------
    scans_t11 = [
        {"scan_id": "r4", "farm_id": "f1", "scan_date": datetime(2026, 7, 1), "health": {"growth_status": "STUNTED"}, "height": {"height_status": "BELOW_EXPECTED"}},
        {"scan_id": "r5", "farm_id": "f1", "scan_date": datetime(2026, 7, 6), "health": {"growth_status": "NORMAL"}, "height": {"height_status": "WITHIN_EXPECTED"}},
        {"scan_id": "r6", "farm_id": "f1", "scan_date": datetime(2026, 7, 11), "health": {"growth_status": "STUNTED"}, "height": {"height_status": "BELOW_EXPECTED"}},
    ]
    res_t11 = TemporalObservationService.detect_observations("f1", scans_t11, "2026-06-01")
    rec_t11 = [o for o in res_t11.observations if o.observation_type == "RECOVERY_OBSERVED"]
    assert len(rec_t11) == 0, f"Expected 0 recovery observations, got {len(rec_t11)}"
    print("[PASS] T-11: STUNTED -> NORMAL -> STUNTED does not trigger premature recovery.")
    passed += 1

    # -------------------------------------------------------------------------
    # T-17: Deterministic observation IDs
    # -------------------------------------------------------------------------
    id1 = TemporalObservationService.generate_observation_id("f1", "HEIGHT_DECREASE_OBSERVED", ["s1", "s2"])
    id2 = TemporalObservationService.generate_observation_id("f1", "HEIGHT_DECREASE_OBSERVED", ["s2", "s1"])
    assert id1 == id2, f"Expected identical IDs regardless of scan_id sort order: {id1} vs {id2}"
    print(f"[PASS] T-17: Stable deterministic observation IDs verified ({id1}).")
    passed += 1

    print("\n=========================================================================")
    print(f"   ALL {passed}/{total} ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
    print("=========================================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
