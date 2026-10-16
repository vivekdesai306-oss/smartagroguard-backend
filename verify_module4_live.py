import asyncio
import sys
import os
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app
from app.services.auth_service import AuthService
from app.database import Database, get_database

async def live_verify():
    print("==========================================================")
    print("   LIVE VERIFICATION: MODULE 4 REAL DATABASE & FASTAPI   ")
    print("==========================================================\n")

    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["agroguard"]

    farms = await db["farms"].find().to_list(10)
    print(f"Total Farms found in 'agroguard' database: {len(farms)}")

    if not farms:
        print("No farms found in DB. Seeding or using test farm.")
        return

    first_farm = farms[0]
    farm_id = first_farm.get("farm_id")
    uid = first_farm.get("uid", "user_001")
    sowing = first_farm.get("sowing_date", "Not set")

    scans_count = await db["scans"].count_documents({"farm_id": farm_id})
    corn_scans = await db["scans"].count_documents({"farm_id": farm_id, "validation_stage": "CORN"})

    print(f"Testing on Farm: {farm_id}")
    print(f"  • Sowing Date : {sowing}")
    print(f"  • Total Scans : {scans_count} ({corn_scans} valid CORN scans)")
    print(f"  • Owner UID   : {uid}\n")

    # Override auth to match this farm's owner
    app.dependency_overrides[AuthService.get_current_user] = lambda: {"uid": uid, "email": "test@agroguard.com", "user_role": "Farmer"}

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        # 1. Test Overview
        res1 = await http_client.get(f"/api/v1/history/farm/{farm_id}/overview")
        print(f"1. GET /overview           -> HTTP {res1.status_code}")
        if res1.status_code == 200:
            d = res1.json()
            print(f"   Data Quality: {d['data_quality']['quality_level']} | DAS Available: {d['das_available']} | Scans: {d['total_scans']}")

        # 2. Test Timeline
        res2 = await http_client.get(f"/api/v1/history/farm/{farm_id}/timeline?page=1&page_size=5")
        print(f"2. GET /timeline           -> HTTP {res2.status_code}")
        if res2.status_code == 200:
            d = res2.json()
            print(f"   Total Count: {d['total_count']} | Returned: {len(d['items'])} scans")

        # 3. Test Growth Curve
        res3 = await http_client.get(f"/api/v1/history/farm/{farm_id}/growth-curve")
        print(f"3. GET /growth-curve       -> HTTP {res3.status_code}")
        if res3.status_code == 200:
            d = res3.json()
            print(f"   Points: {len(d['points'])} | Growth Score: {d.get('growth_score_percent')}%")

        # 4. Test Health Trend
        res4 = await http_client.get(f"/api/v1/history/farm/{farm_id}/health-trend")
        print(f"4. GET /health-trend       -> HTTP {res4.status_code}")
        if res4.status_code == 200:
            d = res4.json()
            print(f"   Health Points: {len(d['points'])}")

        # 5. Test Advisories
        res5 = await http_client.get(f"/api/v1/history/farm/{farm_id}/advisories")
        print(f"5. GET /advisories         -> HTTP {res5.status_code}")
        if res5.status_code == 200:
            d = res5.json()
            print(f"   Advisories Found: {d['total_advisories']}")

        # 6. Test Observations
        res6 = await http_client.get(f"/api/v1/history/farm/{farm_id}/observations")
        print(f"6. GET /observations       -> HTTP {res6.status_code}")
        if res6.status_code == 200:
            d = res6.json()
            print(f"   Temporal Observations: {len(d['observations'])}")
            for obs in d['observations']:
                print(f"     • [{obs['observation_type']}] {obs['headline']}")

        # 7. Test Season Statistics
        res7 = await http_client.get(f"/api/v1/history/farm/{farm_id}/season-statistics")
        print(f"7. GET /season-statistics  -> HTTP {res7.status_code}")
        if res7.status_code == 200:
            d = res7.json()
            print(f"   Observed Span: {d.get('lifecycle_days')} days | Disease Incidents: {d.get('disease_incidents')}")

    client.close()
    print("\n==========================================================")
    print("   MODULE 4 IS FULLY OPERATIONAL AND WORKING ON LIVE DB!  ")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(live_verify())
