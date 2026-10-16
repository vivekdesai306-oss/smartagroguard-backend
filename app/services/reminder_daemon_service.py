"""
Proactive Reminder, Missed Action & Multi-Tier Escalation Daemon Service
Tracks scheduled agronomic tasks (Spraying, Irrigation, Fertigation, Scanning),
detects overdue deadlines, and calculates biological delay costs with escalation warnings.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid

# In-Memory / MongoDB-backed reminder store
REMINDERS_DB: Dict[str, Dict[str, Any]] = {}

class ReminderDaemonService:
    @staticmethod
    def create_reminder(
        farm_id: str,
        action_type: str,
        title: str,
        description: str,
        target_date: str,
        target_window: str = "06:30 AM - 10:30 AM",
        recommended_action: str = ""
    ) -> Dict[str, Any]:
        reminder_id = f"rem_{uuid.uuid4().hex[:8]}"
        item = {
            "reminder_id": reminder_id,
            "farm_id": farm_id,
            "action_type": action_type,
            "title": title,
            "description": description,
            "target_date": target_date,
            "target_window": target_window,
            "status": "UPCOMING",
            "hours_overdue": 0.0,
            "escalation_warning": None,
            "biological_delay_cost": None,
            "recommended_action": recommended_action or description,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }
        REMINDERS_DB[reminder_id] = item
        return item

    @classmethod
    def get_farm_reminders(cls, farm_id: str) -> List[Dict[str, Any]]:
        cls._refresh_overdue_statuses(farm_id)
        return [r for r in REMINDERS_DB.values() if r["farm_id"] == farm_id]

    @classmethod
    def mark_completed(cls, reminder_id: str, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if reminder_id in REMINDERS_DB:
            REMINDERS_DB[reminder_id]["status"] = "COMPLETED"
            REMINDERS_DB[reminder_id]["completed_at"] = datetime.utcnow().isoformat()
            REMINDERS_DB[reminder_id]["escalation_warning"] = None
            return REMINDERS_DB[reminder_id]
        return None

    @classmethod
    def reschedule_reminder(cls, reminder_id: str, new_date: str, new_window: str = "06:30 AM - 10:30 AM") -> Optional[Dict[str, Any]]:
        if reminder_id in REMINDERS_DB:
            REMINDERS_DB[reminder_id]["target_date"] = new_date
            REMINDERS_DB[reminder_id]["target_window"] = new_window
            REMINDERS_DB[reminder_id]["status"] = "UPCOMING"
            REMINDERS_DB[reminder_id]["hours_overdue"] = 0.0
            REMINDERS_DB[reminder_id]["escalation_warning"] = None
            return REMINDERS_DB[reminder_id]
        return None

    @classmethod
    def _refresh_overdue_statuses(cls, farm_id: str):
        """
        Evaluates elapsed time against target dates and updates escalation states.
        """
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        now_dt = datetime.utcnow()

        for r_id, r in REMINDERS_DB.items():
            if r["farm_id"] != farm_id or r["status"] == "COMPLETED":
                continue

            try:
                target_dt = datetime.strptime(r["target_date"], "%Y-%m-%d")
                delta = now_dt - target_dt
                hours_diff = delta.total_seconds() / 3600.0

                if hours_diff > 48.0:
                    r["status"] = "ESCALATED_TIER_2"
                    r["hours_overdue"] = round(hours_diff, 1)
                    r["escalation_warning"] = "🚨 CRITICAL OVERDUE (Tier 2 Escalation): Action delayed by > 48 hours."
                    r["biological_delay_cost"] = cls._get_biological_cost(r["action_type"], tier=2)
                elif hours_diff > 12.0:
                    r["status"] = "ESCALATED_TIER_1"
                    r["hours_overdue"] = round(hours_diff, 1)
                    r["escalation_warning"] = "⚠ OVERDUE (Tier 1 Escalation): Action delayed by > 12 hours."
                    r["biological_delay_cost"] = cls._get_biological_cost(r["action_type"], tier=1)
                elif hours_diff > 0.0:
                    r["status"] = "DUE_NOW"
                    r["hours_overdue"] = round(hours_diff, 1)
                    r["escalation_warning"] = "⏰ Action window currently open today."
                else:
                    r["status"] = "UPCOMING"
                    r["hours_overdue"] = 0.0
            except Exception:
                pass

    @staticmethod
    def _get_biological_cost(action_type: str, tier: int = 1) -> str:
        if action_type == "PESTICIDE_SPRAY":
            if tier >= 2:
                return "Delayed chemical spray allowed foliar fungal lesions to expand by ~35%. Fungal sporulation is now contaminating adjacent stalks."
            return "Postponing protective fungicide application allows airborne spores to penetrate leaf stomata during morning dew."
        elif action_type == "IRRIGATION":
            if tier >= 2:
                return "Delayed irrigation during active vegetative/tasseling stage causes irreversible pollen desiccation and 3-4% yield loss per day."
            return "Moisture tension is rising in the root zone. Stomatal closure is slowing photosynthetic sugar accumulation."
        elif action_type == "FERTIGATION":
            return "Delayed Nitrogen application during rapid stem surge limits internode elongation and reduces final ear cob size."
        else:
            return "Missing the weekly scan milestone delays detection of early-stage foliar pathogens."
