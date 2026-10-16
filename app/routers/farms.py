from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from ..database import get_database
from ..schemas import FarmCreate, FarmOut
from ..services.auth_service import AuthService
from .auth import generate_short_id

router = APIRouter(prefix="/api/v1/farms", tags=["Farms"])

@router.post("", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    farm_id = generate_short_id("f")
    
    new_farm = {
        "farm_id": farm_id,
        "uid": current_user["uid"],
        "farm_address": farm_data.farm_address,
        "farm_area": farm_data.farm_area,
        "active_crop": farm_data.active_crop or "Corn",
        "state": farm_data.state,
        "district": farm_data.district,
        "taluka": farm_data.taluka,
        "village": farm_data.village,
        "entered_latitude": farm_data.entered_latitude,
        "entered_longitude": farm_data.entered_longitude,
        "soil_type": farm_data.soil_type,
        "season": farm_data.season or "KHARIF",
        "sowing_date": farm_data.sowing_date,
        "variety": farm_data.variety
    }
    
    await db["farms"].insert_one(new_farm)
    return new_farm

@router.put("/{farm_id}", response_model=FarmOut)
async def update_farm(
    farm_id: str,
    farm_data: FarmCreate,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    existing = await db["farms"].find_one({"farm_id": farm_id, "uid": current_user["uid"]})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm {farm_id} not found."
        )

    updated_fields = {
        "farm_address": farm_data.farm_address,
        "farm_area": farm_data.farm_area,
        "active_crop": farm_data.active_crop or "Corn",
        "state": farm_data.state,
        "district": farm_data.district,
        "taluka": farm_data.taluka,
        "village": farm_data.village,
        "entered_latitude": farm_data.entered_latitude,
        "entered_longitude": farm_data.entered_longitude,
        "soil_type": farm_data.soil_type,
        "season": farm_data.season or "KHARIF",
        "sowing_date": farm_data.sowing_date,
        "variety": farm_data.variety
    }

    await db["farms"].update_one(
        {"farm_id": farm_id, "uid": current_user["uid"]},
        {"$set": updated_fields}
    )

    updated_doc = await db["farms"].find_one({"farm_id": farm_id, "uid": current_user["uid"]})
    return updated_doc

@router.get("", response_model=List[FarmOut])
async def list_farms(
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    cursor = db["farms"].find({"uid": current_user["uid"]})
    farms = []
    async for document in cursor:
        farms.append(document)
    return farms

@router.get("/reverse-geocode")
def reverse_geocode_location(lat: float, lon: float):
    """
    Translates GPS coordinates into village, city/taluka, district, state, and address.
    """
    from ..services.geocoding_service import GeocodingService
    return GeocodingService.reverse_geocode(lat, lon)

@router.get("/geocode")
def forward_geocode_location(
    village: str = None,
    taluka: str = None,
    district: str = None,
    state: str = None,
    q: str = None
):
    """
    Translates village, city/taluka, district, state into latitude and longitude coordinates.
    """
    from ..services.geocoding_service import GeocodingService
    return GeocodingService.forward_geocode(
        village=village,
        taluka=taluka,
        district=district,
        state=state,
        freeform_query=q
    )

@router.get("/{farm_id}", response_model=FarmOut)
async def get_farm(
    farm_id: str,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    farm = await db["farms"].find_one({"farm_id": farm_id, "uid": current_user["uid"]})
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm {farm_id} not found."
        )
    return farm

@router.delete("/{farm_id}")
async def delete_farm(
    farm_id: str,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    result = await db["farms"].delete_one({"farm_id": farm_id, "uid": current_user["uid"]})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm {farm_id} not found."
        )
    return {"message": f"Farm {farm_id} successfully deleted.", "deleted": True}

