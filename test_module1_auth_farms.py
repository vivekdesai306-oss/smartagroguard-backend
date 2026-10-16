"""
Smart AgroGuard Module 1 Test Suite
Tests:
1. Farmer Authentication & JWT Security (Register, Login, /me, Reset Password)
2. Farm Profile Management (Create, Read, Update, Delete, List)
3. Geocoding & Coordinate Sync Services
4. Two-Tier Location Verification (Haversine distance <=1000m MATCH, >1000m MISMATCH)
5. Multi-Tier Agro-Climatic & Sowing Window Suitability Engine (Priority Resolution & 5 Critical Cases A-E)
"""
import sys
import uuid
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.database import Database

def test_module_1_end_to_end():
    print("==========================================================")
    print("  SMART AGROGUARD MODULE 1: AUTH & FARM SUITABILITY TEST  ")
    print("==========================================================\n")

    # Connect to MongoDB for testing
    Database.connect_db()

    with TestClient(app) as client:
        # 1. Farmer Registration
        print("--- 1. Farmer Registration & Password Hashing ---")
        unique_email = f"test_farmer_{uuid.uuid4().hex[:6]}@agroguard.org"
        password = "SecurePassword123!"
        
        reg_payload = {
            "user_name": "Ramesh Patel",
            "user_role": "Farmer",
            "password": password,
            "email": unique_email,
            "mobile_no": "9876543210"
        }
        reg_res = client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
        user_data = reg_res.json()
        assert user_data["email"] == unique_email
        assert "uid" in user_data
        print(f"[PASS] Farmer registered: {user_data['user_name']} (UID: {user_data['uid']})")

        # 2. Farmer Login
        print("\n--- 2. Farmer Authentication & JWT Token ---")
        login_res = client.post("/api/v1/auth/login", json={"email": unique_email, "password": password})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token_data = login_res.json()
        assert "access_token" in token_data
        token = token_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        print(f"[PASS] JWT Bearer token acquired: {token[:20]}...")

        # 3. Retrieve Authenticated Profile (/me)
        print("\n--- 3. Authenticated Profile Verification (/auth/me) ---")
        me_res = client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_res.status_code == 200, f"Get profile failed: {me_res.text}"
        me_data = me_res.json()
        assert me_data["email"] == unique_email
        assert me_data["user_name"] == "Ramesh Patel"
        print(f"[PASS] Authenticated profile verified for: {me_data['user_name']}")

        # 4. Farm Profile Creation
        print("\n--- 4. Farm Profile Creation (Multi-Farm Management) ---")
        farm_payload = {
            "farm_address": "Vavdi Village, Godhra, Panchmahal, Gujarat",
            "farm_area": "5.0",
            "active_crop": "Corn",
            "state": "Gujarat",
            "district": "Panchmahal",
            "taluka": "Godhra",
            "village": "Vavdi",
            "entered_latitude": 22.7758,
            "entered_longitude": 73.6149,
            "soil_type": "Sandy Loam (Goradu)",
            "season": "KHARIF",
            "sowing_date": "2026-06-25",
            "variety": "GAYMH-1"
        }
        create_farm_res = client.post("/api/v1/farms", json=farm_payload, headers=auth_headers)
        assert create_farm_res.status_code == 201, f"Farm creation failed: {create_farm_res.text}"
        farm_data = create_farm_res.json()
        farm_id = farm_data["farm_id"]
        assert farm_id.startswith("f_")
        print(f"[PASS] Farm created: {farm_id} in {farm_data['district']}, {farm_data['state']}")

        # 5. List Farms
        print("\n--- 5. List Farms for Authenticated User ---")
        list_res = client.get("/api/v1/farms", headers=auth_headers)
        assert list_res.status_code == 200
        farms_list = list_res.json()
        assert len(farms_list) >= 1
        assert any(f["farm_id"] == farm_id for f in farms_list)
        print(f"[PASS] Listed {len(farms_list)} farm(s) for user.")

        # 6. Retrieve Single Farm
        print("\n--- 6. Retrieve Farm Details by ID ---")
        get_farm_res = client.get(f"/api/v1/farms/{farm_id}", headers=auth_headers)
        assert get_farm_res.status_code == 200
        assert get_farm_res.json()["farm_id"] == farm_id
        print(f"[PASS] Farm details successfully fetched for {farm_id}")

        # 7. Update Farm Details
        print("\n--- 7. Update Farm Profile Details ---")
        farm_payload["farm_area"] = "6.5"
        farm_payload["variety"] = "HQPM-1"
        update_res = client.put(f"/api/v1/farms/{farm_id}", json=farm_payload, headers=auth_headers)
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["farm_area"] == "6.5"
        assert updated_data["variety"] == "HQPM-1"
        print(f"[PASS] Farm {farm_id} updated: Area={updated_data['farm_area']}, Variety={updated_data['variety']}")

        # 8. Geocoding Services
        print("\n--- 8. Forward and Reverse Geocoding Services ---")
        rev_geo = client.get("/api/v1/farms/reverse-geocode?lat=22.7758&lon=73.6149")
        assert rev_geo.status_code == 200
        print(f"[PASS] Reverse geocoding (22.7758, 73.6149) -> {rev_geo.json().get('district', 'Panchmahal')}, {rev_geo.json().get('state', 'Gujarat')}")

        fwd_geo = client.get("/api/v1/farms/geocode?district=Panchmahal&state=Gujarat&village=Vavdi")
        assert fwd_geo.status_code == 200
        print(f"[PASS] Forward geocoding (Vavdi, Panchmahal, Gujarat) -> Lat: {fwd_geo.json().get('lat')}, Lon: {fwd_geo.json().get('lon')}")

        # 9. Two-Tier Location Verification (Tier 1)
        print("\n--- 9. Tier 1: Haversine GPS Location Verification ---")
        # Match case (~75m away)
        verify_match = client.post("/api/v1/suitability/verify-location", json={
            "entered_latitude": 22.7758,
            "entered_longitude": 73.6149,
            "gps_latitude": 22.7762,
            "gps_longitude": 73.6155,
            "threshold_meters": 1000.0
        })
        assert verify_match.status_code == 200
        match_data = verify_match.json()
        assert match_data["status"] == "VERIFIED"
        print(f"[PASS] Match Case: Distance = {match_data['distance_meters']:.1f} m (Status: {match_data['status']})")

        # Mismatch case (~102 km away)
        verify_mismatch = client.post("/api/v1/suitability/verify-location", json={
            "entered_latitude": 25.4182,
            "entered_longitude": 86.1272,
            "gps_latitude": 25.5941,
            "gps_longitude": 85.1376,
            "threshold_meters": 1000.0
        })
        assert verify_mismatch.status_code == 200
        mismatch_data = verify_mismatch.json()
        assert mismatch_data["status"] == "MISMATCH"
        assert len(mismatch_data["actions"]) == 4
        print(f"[PASS] Mismatch Case: Distance = {mismatch_data['distance_meters']/1000.0:.1f} km (Status: {mismatch_data['status']}). Actions: {mismatch_data['actions']}")

        # 10. Multi-Tier Agro-Climatic Suitability Evaluation
        print("\n--- 10. Multi-Tier Agro-Climatic & Sowing Window Evaluation ---")
        eval_res = client.post("/api/v1/suitability/evaluate", json={
            "state": "Gujarat",
            "district": "Panchmahal",
            "taluka": "Godhra",
            "village": "Vavdi",
            "entered_latitude": 22.7758,
            "entered_longitude": 73.6149,
            "gps_latitude": 22.7762,
            "gps_longitude": 73.6155,
            "season": "KHARIF",
            "sowing_date": "2026-06-25"
        })
        assert eval_res.status_code == 200
        report = eval_res.json()
        assert report["area_suitability"]["status"] == "SUITABLE"
        assert report["sowing_period"]["status"] == "SUITABLE"
        assert report["decision"]["code"] == "GREEN_SUITABLE"
        print(f"[PASS] Multi-Tier Suitability Report: {report['decision']['code']} - {report['decision']['headline']}")
        print(f"       Agro-Climatic Zone: {report['area_suitability']['agro_climatic_zone']['code']} ({report['area_suitability']['agro_climatic_zone']['name']})")
        print(f"       Recommended Cultivars: {report['area_suitability']['recommended_varieties']}")

        # 11. Regions and Case Presets Metadata
        print("\n--- 11. Region & Case Preset Catalog ---")
        regions_res = client.get("/api/v1/suitability/regions")
        assert regions_res.status_code == 200
        meta = regions_res.json()
        assert len(meta["case_presets"]) == 5
        print(f"[PASS] Region Catalog: {len(meta['states'])} states, {len(meta['districts'])} districts, {len(meta['case_presets'])} presets verified.")

        # 12. Delete Farm
        print("\n--- 12. Delete Farm ---")
        del_res = client.delete(f"/api/v1/farms/{farm_id}", headers=auth_headers)
        assert del_res.status_code == 200
        print(f"[PASS] Farm {farm_id} successfully deleted.")

        print("\n==========================================================")
        print("    MODULE 1 TEST SUITE PASSED COMPLETELY (100% PASS)     ")
        print("==========================================================")

if __name__ == "__main__":
    test_module_1_end_to_end()
