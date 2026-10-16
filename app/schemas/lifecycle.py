"""
Pydantic Schemas for 12-Week Maize Lifecycle Milestones and Timeline
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MilestoneWeekOut(BaseModel):
    week_number: int
    das_start: int
    das_end: int
    growth_stage: str
    stage_title: str
    scan_target: str
    scouting_checklist: List[str]
    agronomic_operations: str
    reminder_copy: str
    urgency: str
    critical_window: bool
    status: str  # COMPLETED / ACTIVE / UPCOMING
    calendar_start_date: str
    calendar_end_date: str
    scans_completed_count: int = 0

class FarmLifecycleTimelineResponse(BaseModel):
    farm_id: str
    sowing_date: str
    current_das: int
    current_week_number: int
    current_stage: str
    total_weeks: int = 12
    progress_pct: float
    active_milestone: MilestoneWeekOut
    all_milestones: List[MilestoneWeekOut]
