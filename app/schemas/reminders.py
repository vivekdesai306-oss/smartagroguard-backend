"""
Pydantic Schemas for Proactive Reminders, Missed Actions, and Escalations
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReminderItem(BaseModel):
    reminder_id: str
    farm_id: str
    action_type: str  # PESTICIDE_SPRAY / IRRIGATION / FERTIGATION / CROP_SCAN / HARVEST
    title: str
    description: str
    target_date: str
    target_window: str  # e.g. "06:00 AM - 10:00 AM"
    status: str  # UPCOMING / DUE_NOW / COMPLETED / OVERDUE / ESCALATED_TIER_1 / ESCALATED_TIER_2
    hours_overdue: float = 0.0
    escalation_warning: Optional[str] = None
    biological_delay_cost: Optional[str] = None
    recommended_action: str
    created_at: str
    completed_at: Optional[str] = None

class ReminderCompleteRequest(BaseModel):
    notes: Optional[str] = None
    completed_date: Optional[str] = None

class ReminderRescheduleRequest(BaseModel):
    new_target_date: str
    new_target_window: Optional[str] = "06:30 AM - 10:30 AM"
    reason: Optional[str] = None

class FarmRemindersResponse(BaseModel):
    farm_id: str
    active_count: int
    overdue_count: int
    reminders: List[ReminderItem]
