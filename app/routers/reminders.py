"""
FastAPI Router for Proactive Action Reminders, Missed Actions, and Escalations
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional

from ..schemas.reminders import (
    ReminderItem,
    ReminderCompleteRequest,
    ReminderRescheduleRequest,
    FarmRemindersResponse
)
from ..services.reminder_daemon_service import ReminderDaemonService

router = APIRouter(prefix="/api/v1/reminders", tags=["Proactive Reminders & Escalations"])

@router.get("/farm/{farm_id}", response_model=FarmRemindersResponse)
def get_farm_reminders(farm_id: str):
    """
    Retrieves all scheduled actions, early alerts, and overdue escalations for a farm parcel.
    """
    reminders = ReminderDaemonService.get_farm_reminders(farm_id)
    
    # If no reminders exist for farm, seed standard initial reminders
    if not reminders:
        r1 = ReminderDaemonService.create_reminder(
            farm_id=farm_id,
            action_type="PESTICIDE_SPRAY",
            title="Scheduled Propiconazole Protective Foliar Spray",
            description="Apply 200 ml Propiconazole 25% EC across your field to protect against Northern Leaf Blight.",
            target_date="2026-10-06",
            target_window="06:30 AM - 10:30 AM",
            recommended_action="Mix 15 ml per 15L tank. Spray during low wind (< 15 km/h) before morning dew evaporates."
        )
        r2 = ReminderDaemonService.create_reminder(
            farm_id=farm_id,
            action_type="IRRIGATION",
            title="Scheduled Drip Irrigation (VT Tasseling Stage)",
            description="Operate drip irrigation pump for 2.5 hours to provide 18,000 Liters of root moisture.",
            target_date="2026-10-05",
            target_window="07:00 AM - 11:00 AM",
            recommended_action="Run drip irrigation lines before mid-day heat."
        )
        r3 = ReminderDaemonService.create_reminder(
            farm_id=farm_id,
            action_type="CROP_SCAN",
            title="Weekly Mandatory Scan #6 (DAS 42)",
            description="Capture standard stalk photo with soil base marker to verify vegetative surge.",
            target_date="2026-10-08",
            target_window="08:00 AM - 12:00 PM",
            recommended_action="Take clean scan under uniform daylight."
        )
        reminders = ReminderDaemonService.get_farm_reminders(farm_id)

    overdue_c = sum(1 for r in reminders if "ESCALATED" in r["status"] or r["status"] == "OVERDUE")
    active_c = sum(1 for r in reminders if r["status"] != "COMPLETED")

    return {
        "farm_id": farm_id,
        "active_count": active_c,
        "overdue_count": overdue_c,
        "reminders": reminders
    }

@router.post("/{reminder_id}/complete", response_model=ReminderItem)
def complete_reminder(reminder_id: str, req: ReminderCompleteRequest = ReminderCompleteRequest()):
    """
    Marks a scheduled farming task as completed.
    """
    res = ReminderDaemonService.mark_completed(reminder_id, notes=req.notes)
    if not res:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return res

@router.post("/{reminder_id}/reschedule", response_model=ReminderItem)
def reschedule_reminder(reminder_id: str, req: ReminderRescheduleRequest):
    """
    Reschedules an overdue or pending farming task.
    """
    res = ReminderDaemonService.reschedule_reminder(reminder_id, new_date=req.new_target_date, new_window=req.new_target_window)
    if not res:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return res
