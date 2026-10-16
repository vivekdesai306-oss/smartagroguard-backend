"""
AgroGuard Module 4 Multi-Channel Farmer Notification Dispatcher
Handles deduplicated alert notifications across SMS, Email, and In-App channels.
Enforces idempotency keys to prevent notification spam.
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from ..schemas.weather import WeatherAlertOut, WeatherSeverity, WeatherAlertType

logger = logging.getLogger("agroguard.notification_service")

class NotificationService:
    """
    Notification dispatch and delivery tracking service.
    Implements SRS Figure 1.8.10 class NotificationService (sendWeatherAlert, sendDiseaseAlert).
    """

    @staticmethod
    def generate_notification_key(
        farm_id: str,
        alert_type: str,
        severity: str,
        timestamp: datetime
    ) -> str:
        """
        Creates an idempotent fingerprint key bucketed by farm, alert, severity, and hour.
        """
        time_bucket = timestamp.strftime("%Y-%m-%d-%H")
        return f"{farm_id}:{alert_type}:{severity}:{time_bucket}"

    @classmethod
    async def dispatch_weather_alert(
        cls,
        db: Any,
        alert: Any,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dispatches weather alert with automatic deduplication.
        """
        # 1. Normal conditions do not generate farmer notifications
        severity_str = alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity)
        alert_type_str = alert.alert_type.value if hasattr(alert.alert_type, "value") else str(alert.alert_type)

        if severity_str == WeatherSeverity.NORMAL.value or alert_type_str == WeatherAlertType.NONE.value:
            return {"status": "SKIPPED", "reason": "NORMAL_WEATHER_NO_NOTIFICATION"}

        # 2. Determine channel
        channel = "SMS" if severity_str == WeatherSeverity.CRITICAL.value else "EMAIL"
        profile = user_profile or {}
        recipient = profile.get("mobile_no" if channel == "SMS" else "email", "farmer@agroguard.com")

        # 3. Generate Idempotency Key
        alert_dt = getattr(alert, "alert_date", datetime.now())
        notif_key = cls.generate_notification_key(alert.farm_id, alert_type_str, severity_str, alert_dt)

        # 4. Check for existing dispatch in this time bucket
        if db is not None:
            existing = await db["notification_delivery_logs"].find_one({
                "notification_key": notif_key,
                "channel": channel,
                "status": "SENT"
            })
            if existing:
                logger.info(f"Deduplicating weather alert notification for key: {notif_key}")
                return {
                    "status": "SKIPPED",
                    "reason": "DUPLICATE_ALERT_SUPPRESSED",
                    "notification_key": notif_key
                }

        # 5. Execute Dispatch (Gateway simulation / SMTP / SMS integration)
        notif_id = f"NT{secrets.token_hex(4).upper()}"
        sent_timestamp = datetime.now()

        delivery_record = {
            "notification_id": notif_id,
            "alert_id": getattr(alert, "alert_id", "WA_PENDING"),
            "farm_id": alert.farm_id,
            "channel": channel,
            "recipient": recipient,
            "notification_key": notif_key,
            "status": "SENT",
            "attempt": 1,
            "sent_at": sent_timestamp,
            "message_title": getattr(alert, "title", f"{severity_str} {alert_type_str} Alert"),
            "message_body": getattr(alert, "message", "Meteorological hazard detected.")
        }

        if db is not None:
            try:
                await db["notification_delivery_logs"].insert_one(delivery_record)
            except Exception as e:
                logger.warning(f"Error logging notification delivery: {e}")

        logger.info(f"Dispatched {channel} notification [{notif_id}] to {recipient} for {alert_type_str}")
        return {
            "status": "SENT",
            "notification_id": notif_id,
            "channel": channel,
            "recipient": recipient,
            "dispatched_at": sent_timestamp.isoformat()
        }

    @classmethod
    async def get_delivery_logs(cls, db: Any, farm_id: str) -> List[Dict[str, Any]]:
        if db is None:
            return []
        cursor = db["notification_delivery_logs"].find({"farm_id": farm_id}).sort("sent_at", -1).limit(50)
        logs = await cursor.to_list(length=50)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
