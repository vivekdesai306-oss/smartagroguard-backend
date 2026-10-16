import sys
import os
import asyncio
from datetime import datetime, timedelta
import httpx

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.services.auth_service import AuthService
from app.database import Database, get_database

TEST_USER = {
    "uid": "test_farmer_001",
    "user_name": "Test Farmer",
    "email": "farmer@test.com",
    "user_role": "Farmer"
}

app.dependency_overrides[AuthService.get_current_user] = lambda: TEST_USER

async def setup_test_data(db):
    farm_id = "farm_test_history_001"
    await db["farms"].delete_many({"farm_id": farm_id})
    await db["scans"].delete_many({"farm_id": farm_id})

    await db["farms"].insert_one({
        "farm_id": farm_id,
        "uid": TEST_USER["uid"],
        "farm_address": "Vavdi, Godhra, Panchmahal, Gujarat",
        "farm_area": "2.5 Acres",
        "crop_type": "Corn",
        "variety": "GAYMH-1",
        "season": "KHARIF",
        "soil_type": "Sandy Loam (Goradu)",
        "sowing_date": "2026-06-01"
    })

    base_date = datetime(2026, 6, 15)
    test_scans = [
        {
            "scan_id": "scan_01",
            "farm_id": farm_id,
            "validation_stage": "CORN",
            "scan_date": base_date,
            "day_count": 14,
            "image_url": "/uploads/test1.jpg",
            "growth": {"visual_week": "Week 2"},
            "height": {"measured_height_cm": 12.0, "height_status": "WITHIN_EXPECTED"},
            "health": {"growth_status": "NORMAL"},
            "disease_log": {"detected_disease": "Healthy", "confidence_score": 0.95},
            "module3_advisory": {"recommendation_status": "MAINTENANCE", "farmer_summary": "Apply basal starter NPK."}
        },
        {
            "scan_id": "scan_02",
            "farm_id": farm_id,
            "validation_stage": "CORN",
            "scan_date": base_date + timedelta(days=11),
            "day_count": 25,
            "image_url": "/uploads/test2.jpg",
            "growth": {"visual_week": "Week 4"},
            "height": {"measured_height_cm": 22.0, "height_status": "BELOW_EXPECTED"},
            "health": {"growth_status": "STUNTED"},
            "disease_log": {"detected_disease": "Healthy", "confidence_score": 0.90},
            "module3_advisory": {
                "recommendation_status": "RESTORE_WATER_AVAILABILITY",
                "farmer_summary": "Restore soil moisture before applying urea.",
                "non_chemical_action": {"action_type": "RESTORE_WATER_AVAILABILITY"}
            }
        },
        {
            "scan_id": "scan_03",
            "farm_id": farm_id,
            "validation_stage": "CORN",
            "scan_date": base_date + timedelta(days=18),
            "day_count": 32,
            "image_url": "/uploads/test3.jpg",
            "growth": {"visual_week": "Week 5"},
            "height": {"measured_height_cm": 34.0, "height_status": "BELOW_EXPECTED"},
            "health": {"growth_status": "STUNTED_AND_INFECTED"},
            "disease_log": {"detected_disease": "Corn Common Rust", "confidence_score": 0.88},
            "module3_advisory": {
                "recommendation_status": "TREATMENT_RECOMMENDED",
                "farmer_summary": "Spray Amistar Top for foliar rust.",
                "pesticide_treatment": {"product_name": "Amistar Top"}
            }
        },
        {
            "scan_id": "scan_04",
            "farm_id": farm_id,
            "validation_stage": "CORN",
            "scan_date": base_date + timedelta(days=24),
            "day_count": 38,
            "image_url": "/uploads/test4.jpg",
            "growth": {"visual_week": "Week 6"},
            "height": {"measured_height_cm": 40.0, "height_status": "BELOW_EXPECTED"},
            "health": {"growth_status": "INFECTED"},
            "disease_log": {"detected_disease": "Corn Common Rust", "confidence_score": 0.85},
            "module3_advisory": {
                "recommendation_status": "MONITOR_SCOUT",
                "farmer_summary": "Monitor rust progression after spray."
            }
        },
        {
            "scan_id": "scan_05",
            "farm_id": farm_id,
            "validation_stage": "CORN",
            "scan_date": base_date + timedelta(days=32),
            "day_count": 46,
            "image_url": "/uploads/test5.jpg",
            "growth": {"visual_week": "Week 7"},
            "height": {"measured_height_cm": 135.0, "height_status": "WITHIN_EXPECTED"},
            "health": {"growth_status": "NORMAL"},
            "disease_log": {"detected_disease": "Healthy", "confidence_score": 0.94},
            "module3_advisory": {
                "recommendation_status": "MAINTENANCE",
                "farmer_summary": "Maintain tassel irrigation."
            }
        },
        {
            "scan_id": "scan_06",
            "farm_id": farm_id,
            "validation_stage": "CORN",
            "scan_date": base_date + timedelta(days=39),
            "day_count": 53,
            "image_url": "/uploads/test6.jpg",
            "growth": {"visual_week": "Week 8"},
            "height": {"measured_height_cm": 175.0, "height_status": "WITHIN_EXPECTED"},
            "health": {"growth_status": "NORMAL"},
            "disease_log": {"detected_disease": "Healthy", "confidence_score": 0.96},
            "module3_advisory": {
                "recommendation_status": "MAINTENANCE",
                "farmer_summary": "Maintain silking moisture."
            }
        },
        {
            "scan_id": "scan_rejected",
            "farm_id": farm_id,
            "validation_stage": "NOT_CORN",
            "scan_date": base_date + timedelta(days=40),
            "day_count": 54,
            "image_url": "/uploads/weed.jpg"
        }
    ]
    await db["scans"].insert_many(test_scans)
    return farm_id

async def run_api_tests():
    print("=========================================================================")
    print("   RUNNING MODULE 4 FASTAPI ROUTER INTEGRATION & ENDPOINT TESTS          ")
    print("=========================================================================\n")

    Database.connect_db()
    db = get_database()
    farm_id = await setup_test_data(db)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /overview
        res_ov = await client.get(f"/api/v1/history/farm/{farm_id}/overview")
        assert res_ov.status_code == 200, f"Overview status {res_ov.status_code}: {res_ov.text}"
        ov_data = res_ov.json()
        assert ov_data["farm_id"] == farm_id
        assert ov_data["total_scans"] == 6
        assert ov_data["crop_type"] == "Corn"
        assert ov_data["das_available"] is True
        assert "data_quality" in ov_data
        assert "generated_at" in ov_data
        print(f"[PASS] 1. GET /overview: Total Scans={ov_data['total_scans']} (6 CORN, rejected excluded), Stage={ov_data['latest_growth_week']}.")

        # 2. GET /timeline (paginated + date filtered)
        res_tl = await client.get(f"/api/v1/history/farm/{farm_id}/timeline?page=1&page_size=3")
        assert res_tl.status_code == 200
        tl_data = res_tl.json()
        assert tl_data["total_count"] == 6
        assert len(tl_data["items"]) == 3
        assert tl_data["page"] == 1
        assert tl_data["page_size"] == 3
        assert tl_data["items"][0]["scan_id"] == "scan_01"
        print(f"[PASS] 2. GET /timeline (pagination): Page 1 of 2 retrieved (3 of 6 items).")

        res_tl_f = await client.get(f"/api/v1/history/farm/{farm_id}/timeline?start_date=2026-07-01")
        assert res_tl_f.status_code == 200
        tl_f_data = res_tl_f.json()
        assert tl_f_data["total_count"] > 0
        print(f"[PASS] 2b. GET /timeline (date filter): Filtered scans returned ({tl_f_data['total_count']} items).")

        # 3. GET /growth-curve
        res_gc = await client.get(f"/api/v1/history/farm/{farm_id}/growth-curve")
        assert res_gc.status_code == 200
        gc_data = res_gc.json()
        assert len(gc_data["points"]) == 6
        assert gc_data["valid_height_scans"] == 6
        assert gc_data["growth_score_available"] is True
        assert gc_data["growth_score_percent"] == 50.0
        print(f"[PASS] 3. GET /growth-curve: 6 points mapped, Growth Score={gc_data['growth_score_percent']}%.")

        # 4. GET /health-trend
        res_ht = await client.get(f"/api/v1/history/farm/{farm_id}/health-trend")
        assert res_ht.status_code == 200
        ht_data = res_ht.json()
        assert len(ht_data["points"]) == 6
        print(f"[PASS] 4. GET /health-trend: 6 multimodal health progression states retrieved.")

        # 5. GET /advisories
        res_adv = await client.get(f"/api/v1/history/farm/{farm_id}/advisories")
        assert res_adv.status_code == 200
        adv_data = res_adv.json()
        assert adv_data["total_advisories"] == 6
        assert any(a["has_chemical_treatment"] for a in adv_data["items"])
        assert any(a["has_non_chemical_action"] for a in adv_data["items"])
        print(f"[PASS] 5. GET /advisories: {adv_data['total_advisories']} historical advisories cataloged with chemical & cultural tags.")

        # 6. GET /observations
        res_obs = await client.get(f"/api/v1/history/farm/{farm_id}/observations")
        assert res_obs.status_code == 200
        obs_data = res_obs.json()
        obs_list = obs_data["observations"]

        has_rust_persistence = any(
            o["observation_type"] == "DISEASE_PERSISTENCE_OBSERVED" and "Rust" in o["headline"]
            for o in obs_list
        )
        has_recovery = any(
            o["observation_type"] == "RECOVERY_OBSERVED"
            for o in obs_list
        )
        assert has_rust_persistence, "Expected Rust disease persistence observation"
        assert has_recovery, "Expected recovery observation after 2 consecutive normals"
        print(f"[PASS] 6. GET /observations: Temporal change detection verified (Disease persistence & Recovery confirmed).")

        # 7. GET /season-statistics
        res_stat = await client.get(f"/api/v1/history/farm/{farm_id}/season-statistics")
        assert res_stat.status_code == 200
        stat_data = res_stat.json()
        assert stat_data["total_scans"] == 6
        assert stat_data["disease_incidents"] == 2
        assert "Corn Common Rust" in stat_data["unique_diseases"]
        assert stat_data["chemical_advisories"] >= 1
        assert stat_data["non_chemical_advisories"] >= 1
        print(f"[PASS] 7. GET /season-statistics: End-of-season summary compiled: {stat_data['disease_incidents']} disease incidents, {stat_data['total_advisories']} advisories.")

        # 8. Farm Ownership Security Check
        res_unauth = await client.get("/api/v1/history/farm/farm_unauthorized_999/overview")
        assert res_unauth.status_code == 404
        print("[PASS] 8. Unauthorized farm access safely rejected with HTTP 404.")

    # Cleanup test data
    await db["farms"].delete_many({"farm_id": farm_id})
    await db["scans"].delete_many({"farm_id": farm_id})
    Database.close_db()

    print("\n=========================================================================")
    print("   ALL 8 MODULE 4 API ENDPOINT INTEGRATION TESTS PASSED!                 ")
    print("=========================================================================")

if __name__ == "__main__":
    asyncio.run(run_api_tests())
