"""
12-Week Maize Lifecycle Timeline & Weekly Scan Roadmap Service
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from ..data.lifecycle_milestones_data import LIFECYCLE_MILESTONES

class LifecycleTimelineService:
    @classmethod
    def get_farm_timeline(
        cls,
        farm_id: str,
        sowing_date_str: str,
        completed_scans_das: List[int] = []
    ) -> Dict[str, Any]:
        """
        Builds a customized 12-week timeline mapped to actual calendar dates from sowing_date.
        """
        try:
            sow_dt = datetime.strptime(sowing_date_str, "%Y-%m-%d")
        except Exception:
            sow_dt = datetime.utcnow() - timedelta(days=45)
            sowing_date_str = sow_dt.strftime("%Y-%m-%d")

        today_dt = datetime.utcnow()
        current_das = max(0, (today_dt - sow_dt).days)

        current_week_num = min(12, max(1, (current_das // 7) + 1))
        
        milestones_out = []
        active_milestone = None

        for m in LIFECYCLE_MILESTONES:
            w_num = m["week_number"]
            start_dt = sow_dt + timedelta(days=m["das_start"])
            end_dt = sow_dt + timedelta(days=m["das_end"])

            # Status
            if current_das > m["das_end"]:
                status = "COMPLETED"
            elif current_das >= m["das_start"] and current_das <= m["das_end"]:
                status = "ACTIVE"
            else:
                status = "UPCOMING"

            # Check if any scans fall in this DAS range
            scans_in_week = sum(1 for d in completed_scans_das if m["das_start"] <= d <= m["das_end"])

            item = {
                "week_number": w_num,
                "das_start": m["das_start"],
                "das_end": m["das_end"],
                "growth_stage": m["growth_stage"],
                "stage_title": m["stage_title"],
                "scan_target": m["scan_target"],
                "scouting_checklist": m["scouting_checklist"],
                "agronomic_operations": m["agronomic_operations"],
                "reminder_copy": m["reminder_copy"],
                "urgency": m["urgency"],
                "critical_window": m["critical_window"],
                "status": status,
                "calendar_start_date": start_dt.strftime("%b %d, %Y"),
                "calendar_end_date": end_dt.strftime("%b %d, %Y"),
                "scans_completed_count": scans_in_week
            }

            milestones_out.append(item)
            if status == "ACTIVE":
                active_milestone = item

        if not active_milestone:
            active_milestone = milestones_out[-1] if current_das > 95 else milestones_out[0]

        progress_pct = min(100.0, round((current_das / 115.0) * 100.0, 1))

        return {
            "farm_id": farm_id,
            "sowing_date": sowing_date_str,
            "current_das": current_das,
            "current_week_number": current_week_num,
            "current_stage": active_milestone["growth_stage"],
            "total_weeks": 12,
            "progress_pct": progress_pct,
            "active_milestone": active_milestone,
            "all_milestones": milestones_out
        }
