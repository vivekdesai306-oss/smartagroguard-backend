"""
FastAPI Router for 12-Week Maize Lifecycle Timeline & Weekly Scan Roadmap
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional

from ..schemas.lifecycle import FarmLifecycleTimelineResponse
from ..services.lifecycle_timeline_service import LifecycleTimelineService
from ..data.lifecycle_milestones_data import LIFECYCLE_MILESTONES

router = APIRouter(prefix="/api/v1/lifecycle", tags=["12-Week Lifecycle & Scan Roadmap"])

@router.get("/timeline/{farm_id}", response_model=FarmLifecycleTimelineResponse)
def get_lifecycle_timeline(
    farm_id: str,
    sowing_date: Optional[str] = Query("2026-06-28", description="Farm sowing date (YYYY-MM-DD)")
):
    """
    Retrieves the complete 12-week maize journey mapped to calendar dates,
    milestone scouting checklists, and scan completion badges.
    """
    return LifecycleTimelineService.get_farm_timeline(
        farm_id=farm_id,
        sowing_date_str=sowing_date,
        completed_scans_das=[7, 14, 21, 28, 35, 42] # sample completed scans
    )

@router.get("/milestones")
def get_all_milestones():
    """
    Returns the master template of all 12 weekly phenological milestones.
    """
    return LIFECYCLE_MILESTONES
