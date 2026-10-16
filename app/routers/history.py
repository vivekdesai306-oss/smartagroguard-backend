import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_database
from ..services.auth_service import AuthService
from ..services.history_service import HistoryService
from ..services.growth_analytics_service import GrowthAnalyticsService
from ..services.temporal_observation_service import TemporalObservationService
from ..services.season_summary_service import SeasonSummaryService
from ..schemas import (
    SeasonOverviewResponse,
    TimelineResponse,
    GrowthCurveResponse,
    HealthTrendResponse,
    AdvisoryHistoryResponse,
    ObservationsResponse,
    SeasonStatisticsResponse
)

logger = logging.getLogger("agroguard.routers.history")

router = APIRouter(prefix="/api/v1/history", tags=["Module 4: Crop Lifecycle History & Analytics"])

async def verify_farm_ownership(
    farm_id: str,
    current_user: dict,
    db: AsyncIOMotorDatabase
) -> dict:
    farm = await db["farms"].find_one({"farm_id": farm_id, "uid": current_user["uid"]})
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with id {farm_id} not found under your profile."
        )
    return farm

@router.get("/farm/{farm_id}/overview", response_model=SeasonOverviewResponse)
async def get_season_overview(
    farm_id: str,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns quick-glance current operational metrics for the dashboard header.
    """
    farm = await verify_farm_ownership(farm_id, current_user, db)
    scans = await HistoryService.get_all_valid_scans(farm_id, db)
    return SeasonSummaryService.build_overview(farm_id, scans, farm)

@router.get("/farm/{farm_id}/timeline", response_model=TimelineResponse)
async def get_timeline(
    farm_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns paginated chronological scan entries with recalculated DAS and data quality metrics.
    """
    farm = await verify_farm_ownership(farm_id, current_user, db)
    return await HistoryService.get_timeline(
        farm_id=farm_id,
        farm=farm,
        db=db,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/farm/{farm_id}/growth-curve", response_model=GrowthCurveResponse)
async def get_growth_curve(
    farm_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns chronological measured stalk heights vs expected biological benchmark bands.
    """
    farm = await verify_farm_ownership(farm_id, current_user, db)
    scans = await HistoryService.get_all_valid_scans(farm_id, db, start_date, end_date)
    return await GrowthAnalyticsService.build_growth_curve(farm_id, scans, farm, db)

@router.get("/farm/{farm_id}/health-trend", response_model=HealthTrendResponse)
async def get_health_trend(
    farm_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns chronological disease detections and multimodal health states over time.
    """
    farm = await verify_farm_ownership(farm_id, current_user, db)
    scans = await HistoryService.get_all_valid_scans(farm_id, db, start_date, end_date)
    return await GrowthAnalyticsService.build_health_trend(farm_id, scans, farm)

@router.get("/farm/{farm_id}/advisories", response_model=AdvisoryHistoryResponse)
async def get_advisories(
    farm_id: str,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Returns all historical agronomic advisories issued across the crop lifecycle.
    """
    farm = await verify_farm_ownership(farm_id, current_user, db)
    return await HistoryService.get_advisories(farm_id, farm, db)

@router.get("/farm/{farm_id}/observations", response_model=ObservationsResponse)
async def get_temporal_observations(
    farm_id: str,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Performs single-pass temporal change detection (height change, disease persistence, recovery).
    """
    farm = await verify_farm_ownership(farm_id, current_user, db)
    scans = await HistoryService.get_all_valid_scans(farm_id, db)
    return TemporalObservationService.detect_observations(farm_id, scans, farm.get("sowing_date"))

@router.get("/farm/{farm_id}/season-statistics", response_model=SeasonStatisticsResponse)
async def get_season_statistics(
    farm_id: str,
    current_user: dict = Depends(AuthService.get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Computes holistic end-of-season descriptive metrics, growth scores, and intervals.
    """
    farm = await verify_farm_ownership(farm_id, current_user, db)
    scans = await HistoryService.get_all_valid_scans(farm_id, db)
    return SeasonSummaryService.build_statistics(farm_id, scans, farm)
