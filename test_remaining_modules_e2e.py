"""
Smart AgroGuard - Comprehensive Remaining Modules Verification Suite
Validates:
1. Knapsack Sprayer Dilution & CIBRC Chemical Engine (Module 3 Precision Dosage)
2. FAO-56 Penman-Monteith Evapotranspiration & Smart Irrigation Engine (Module 3/5 Irrigation)
3. Proactive Reminders, Missed Action Tracking & Multi-Tier Escalations
4. 5-Pillar Optimal Harvest Readiness & Post-Harvest Storage Advisor (Module 6)
5. 12-Week Farmer Lifecycle Calendar & Weekly Scan Milestones (Module 6)
6. Pest Vector Linkage Engine & Secondary Rot Vulnerabilities
7. Multi-Temporal Treatment Efficacy & Lesion Recovery Engine
8. MiDaS Monocular Depth Estimation & Stalk Height Geometry
"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.services.dilution_calculator_service import DilutionCalculatorService
from app.services.irrigation_service import IrrigationService
from app.services.pest_vector_engine import PestVectorEngine
from app.services.reminder_daemon_service import ReminderDaemonService
from app.services.harvest_readiness_service import HarvestReadinessService
from app.services.lifecycle_timeline_service import LifecycleTimelineService
from app.services.treatment_efficacy_service import TreatmentEfficacyService
from app.services.depth_estimation_service import DepthEstimationService

def run_comprehensive_tests():
    print("=========================================================================")
    print("   SMART AGROGUARD COMPREHENSIVE REMAINING MODULES VERIFICATION SUITE    ")
    print("=========================================================================\n")

    with TestClient(app) as client:
        # 1. Knapsack Sprayer Dilution Calculator & CIBRC Chemicals
        print("--- 1. Testing Knapsack Sprayer & CIBRC Chemical Engine ---")
        dosage_payload = {
            "chemical_id": "PROPICONAZOLE_25_EC",
            "area_acres": 2.5,
            "tank_capacity_liters": 15.0,
            "water_volume_per_acre_liters": 200.0
        }
        res_dose = client.post("/api/v1/dosage/calculate", json=dosage_payload)
        assert res_dose.status_code == 200, f"Dosage calculation failed: {res_dose.text}"
        data_dose = res_dose.json()
        assert data_dose["total_water_liters"] == 500.0
        assert data_dose["total_tanks_required"] == 34
        assert data_dose["chemical_per_tank"] == 15.0
        assert data_dose["total_chemical_needed"] == 500.0
        assert data_dose["phi_days"] == 30
        print(f"[PASS] Knapsack Dilution: {data_dose['area_acres']} acres -> {data_dose['total_tanks_required']} tanks (15L each), {data_dose['chemical_per_tank']} ml/tank, PHI: {data_dose['phi_days']} days.")

        chem_list_res = client.get("/api/v1/dosage/chemicals")
        assert chem_list_res.status_code == 200
        chems = chem_list_res.json()
        assert len(chems) >= 8
        print(f"[PASS] CIBRC Chemicals Catalog: {len(chems)} registered formulations verified.")

        # 2. FAO-56 Penman-Monteith Smart Irrigation Engine
        print("\n--- 2. Testing FAO-56 Penman-Monteith Evapotranspiration & Water Budgeting ---")
        irrig_payload = {
            "area_acres": 3.0,
            "soil_type": "Sandy Loam (Goradu)",
            "das": 48, # Mid-season VT Tasseling stage (Peak Kc = 1.15)
            "temperature_c": 32.0,
            "humidity_percent": 60,
            "wind_speed_kmh": 9.0,
            "solar_radiation_mj": 20.0,
            "rainfall_7d_mm": 2.0,
            "irrigation_method": "Drip"
        }
        res_irrig = client.post("/api/v1/irrigation/calculate", json=irrig_payload)
        assert res_irrig.status_code == 200, f"Irrigation calculation failed: {res_irrig.text}"
        data_irrig = res_irrig.json()
        assert data_irrig["kc_crop_coefficient"] == 1.15
        assert data_irrig["et0_reference_mm_per_day"] > 3.0
        assert data_irrig["etc_crop_water_demand_mm_per_day"] > 4.0
        assert data_irrig["total_water_volume_liters"] > 10000.0
        assert data_irrig["recommended_runtime_hours"] > 0.0
        print(f"[PASS] FAO-56 Engine: DAS={data_irrig['das']} (Stage: {data_irrig['growth_stage_name']}), Kc={data_irrig['kc_crop_coefficient']}, ET0={data_irrig['et0_reference_mm_per_day']} mm/d, ETc={data_irrig['etc_crop_water_demand_mm_per_day']} mm/d, Volume={data_irrig['total_water_volume_liters']} L, Drip Runtime={data_irrig['recommended_runtime_hours']}h.")

        # Ingest IoT Soil Telemetry
        res_telemetry = client.post("/api/v1/irrigation/telemetry/soil", json={
            "farm_id": "f_test123",
            "sensor_id": "PROBE_01",
            "depth_cm": 15,
            "volumetric_water_content_pct": 24.5,
            "soil_temperature_c": 28.2
        })
        assert res_telemetry.status_code == 200
        print(f"[PASS] IoT Telemetry Ingestion: VWC=24.5% @ 15cm depth successfully ingested.")

        # 3. Proactive Reminders & Escalations
        print("\n--- 3. Testing Action Reminders & Multi-Tier Escalations ---")
        rem_res = client.get("/api/v1/reminders/farm/f_test123")
        assert rem_res.status_code == 200
        rem_data = rem_res.json()
        assert rem_data["active_count"] >= 1
        first_rem = rem_data["reminders"][0]
        print(f"[PASS] Farm Reminders: {len(rem_data['reminders'])} tasks active. Top task: '{first_rem['title']}' ({first_rem['status']}).")

        # Mark completed
        comp_res = client.post(f"/api/v1/reminders/{first_rem['reminder_id']}/complete", json={"notes": "Sprayed 200ml Tilt with knapsack."})
        assert comp_res.status_code == 200
        assert comp_res.json()["status"] == "COMPLETED"
        print(f"[PASS] Reminder Completion: Task {first_rem['reminder_id']} transitioned to COMPLETED.")

        # 4. Multi-Criteria Optimal Harvest Readiness
        print("\n--- 4. Testing 5-Pillar Harvest Readiness Decision Engine ---")
        # Ready case (All 5 pass)
        harvest_ready_payload = {
            "farm_id": "f_test123",
            "das": 105,
            "growth_stage": "R6",
            "cumulative_gdd": 1520.0,
            "estimated_grain_moisture_pct": 17.5,
            "last_chemical_spray_date": "2026-08-15", # > 30 days ago
            "last_chemical_id": "PROPICONAZOLE_25_EC",
            "forecast_rain_next_3_days_mm": 0.0
        }
        res_h_ready = client.post("/api/v1/harvest/evaluate", json=harvest_ready_payload)
        assert res_h_ready.status_code == 200
        d_h_ready = res_h_ready.json()
        assert d_h_ready["overall_status"] == "GREEN_LIGHT_HARVEST"
        assert d_h_ready["is_ready_for_harvest"] == True
        assert d_h_ready["harvest_readiness_score_pct"] == 100.0
        print(f"[PASS] Harvest Readiness (Pass): {d_h_ready['overall_status']} (Score: {d_h_ready['harvest_readiness_score_pct']}%) - {d_h_ready['headline']}.")

        # PHI Hold Case
        harvest_phi_hold_payload = {
            "farm_id": "f_test123",
            "das": 105,
            "growth_stage": "R6",
            "cumulative_gdd": 1520.0,
            "estimated_grain_moisture_pct": 17.5,
            "last_chemical_spray_date": "2026-10-01", # Only 4 days ago (Requires 30 days)
            "last_chemical_id": "PROPICONAZOLE_25_EC",
            "forecast_rain_next_3_days_mm": 0.0
        }
        res_h_phi = client.post("/api/v1/harvest/evaluate", json=harvest_phi_hold_payload)
        assert res_h_phi.status_code == 200
        d_h_phi = res_h_phi.json()
        assert d_h_phi["overall_status"] == "CHEMICAL_PHI_HOLD"
        assert d_h_phi["is_ready_for_harvest"] == False
        print(f"[PASS] Harvest Readiness (PHI Hold): {d_h_phi['overall_status']} - {d_h_phi['headline']}. Days remaining: {d_h_phi['phi_countdown_days_remaining']}.")

        # 5. 12-Week Maize Lifecycle Timeline
        print("\n--- 5. Testing 12-Week Farmer Lifecycle Calendar & Roadmap ---")
        life_res = client.get("/api/v1/lifecycle/timeline/f_test123?sowing_date=2026-06-28")
        assert life_res.status_code == 200
        d_life = life_res.json()
        assert len(d_life["all_milestones"]) == 12
        assert d_life["current_week_number"] >= 1
        print(f"[PASS] 12-Week Lifecycle: Sowing={d_life['sowing_date']}, Current DAS={d_life['current_das']}, Active Stage={d_life['current_stage']}, Total Milestones={len(d_life['all_milestones'])}.")

        # 6. Pest Vector Correlation Engine
        print("\n--- 6. Testing Pest Vector Linkage & Secondary Infection Engine ---")
        vec_res = PestVectorEngine.evaluate_vector_risk(
            observed_pests=["FALL_ARMYWORM"],
            observed_symptoms=["frass", "whorl_holes"],
            has_whorl_damage=True
        )
        assert vec_res["has_vector_activity"] == True
        assert len(vec_res["elevated_disease_risks"]) >= 1
        print(f"[PASS] Vector Linkage: Detected '{vec_res['detected_vectors']}', Secondary Risks: {[r['pest'] for r in vec_res['elevated_disease_risks']]}.")

        # 7. Multi-Temporal Treatment Efficacy
        print("\n--- 7. Testing Treatment Efficacy & Lesion Recovery Tracking ---")
        pre_scan_mock = {"scan_id": "S001", "disease_analysis": {"detected_disease": "Northern Leaf Blight", "affected_area_ratio": 0.16}}
        post_scan_mock = {"scan_id": "S002", "disease_analysis": {"detected_disease": "Healthy", "affected_area_ratio": 0.02}}
        eff_res = TreatmentEfficacyService.compare_treatment_efficacy(pre_scan_mock, post_scan_mock, "Propiconazole 25% EC")
        assert eff_res["lesion_reduction_pct"] > 80.0
        assert eff_res["efficacy_rating"] == "HIGHLY_EFFECTIVE"
        print(f"[PASS] Treatment Efficacy: Lesion reduction={eff_res['lesion_reduction_pct']}%, Rating={eff_res['efficacy_rating']}.")

        # 8. Monocular Depth Stalk Height Estimation
        print("\n--- 8. Testing MiDaS Monocular Depth Height Estimation ---")
        depth_res = DepthEstimationService.estimate_depth_and_height(crop_stage="Week 6", das=42)
        assert depth_res["estimated_stalk_height_cm"] > 80.0
        assert depth_res["marker_free_status"] == "MARKERLESS_CALIBRATED"
        print(f"[PASS] Monocular Depth: Markerless Stalk Height={depth_res['estimated_stalk_height_cm']} cm, Method={depth_res['method']}.")

        print("\n=========================================================================")
        print("   ALL REMAINING MODULE TESTS PASSED COMPLETELY (100% SUCCESS)           ")
        print("=========================================================================")

if __name__ == "__main__":
    run_comprehensive_tests()
