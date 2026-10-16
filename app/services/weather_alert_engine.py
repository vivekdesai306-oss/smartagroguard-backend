"""
AgroGuard Module 4 Biological Weather Alert Engine
Evaluates atmospheric conditions against Maize (Zea mays L.) physiological stress thresholds.
Generates Table 1.6.7 alert payloads with strict agronomic guidance.
"""

import secrets
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..weather_config import (
    FROST_FREEZE_C,
    FROST_CRITICAL_C,
    FROST_ADVISORY_C,
    HEAVY_RAIN_WARNING_24H_MM,
    HEAVY_RAIN_CRITICAL_24H_MM,
    HIGH_HUMIDITY_PERCENT,
    HIGH_HUMIDITY_MIN_DURATION_HOURS,
    FUNGAL_TEMP_MIN_C,
    FUNGAL_TEMP_MAX_C
)
from ..schemas.weather import (
    HourlyForecastPoint,
    WeatherAlertType,
    WeatherSeverity,
    WeatherSourceStatus,
    WeatherAlertCreate,
    WeatherAlertOut,
    WeatherRiskAssessment
)

logger = logging.getLogger("agroguard.weather_alert_engine")

class WeatherAlertEngine:
    """
    Biological crop stress and early warning rule evaluator.
    Strictly outputs environmental risk flags and operational warnings without diagnosing plant disease.
    """

    @staticmethod
    def evaluate_frost_risk(hourly: List[HourlyForecastPoint]) -> Optional[WeatherRiskAssessment]:
        if not hourly:
            return None
        
        min_temp = min(h.temperature_c for h in hourly[:24])
        first_h = hourly[0].timestamp
        last_h = hourly[min(23, len(hourly) - 1)].timestamp

        if min_temp <= FROST_FREEZE_C:
            return WeatherRiskAssessment(
                alert_type=WeatherAlertType.FROST,
                severity=WeatherSeverity.CRITICAL,
                risk_score=1.0,
                reasons=[f"Sub-zero freeze hazard ({min_temp:.1f}°C) forecast in next 24 hours."],
                guidance=[
                    "Severe freeze risk: Cell membrane rupture and irreversible leaf whorl damage expected.",
                    "Initiate defensive furrow irrigation or active thermal smudging prior to midnight."
                ],
                valid_from=first_h,
                valid_until=last_h
            )
        elif min_temp <= FROST_CRITICAL_C:
            return WeatherRiskAssessment(
                alert_type=WeatherAlertType.FROST,
                severity=WeatherSeverity.CRITICAL,
                risk_score=0.9,
                reasons=[f"Critical Frost-Risk: Minimum temperature ({min_temp:.1f}°C) is at or below {FROST_CRITICAL_C}°C threshold."],
                guidance=[
                    "Protect sensitive nursery seedlings and young vegetative whorls.",
                    "Apply light surface irrigation before dawn; latent heat release buffers soil boundary temperatures."
                ],
                valid_from=first_h,
                valid_until=last_h
            )
        elif min_temp <= FROST_ADVISORY_C:
            return WeatherRiskAssessment(
                alert_type=WeatherAlertType.FROST,
                severity=WeatherSeverity.ADVISORY,
                risk_score=0.5,
                reasons=[f"Frost Advisory: Minimum temperature ({min_temp:.1f}°C) approaching chilling injury window."],
                guidance=[
                    "Monitor overnight temperatures closely.",
                    "Prepare protective nursery shading or mulching if temperatures trend further downward."
                ],
                valid_from=first_h,
                valid_until=last_h
            )
        return None

    @staticmethod
    def evaluate_heavy_rain(hourly: List[HourlyForecastPoint]) -> Optional[WeatherRiskAssessment]:
        if not hourly:
            return None
        
        rain_24h = sum(h.rainfall_mm for h in hourly[:24])
        first_h = hourly[0].timestamp
        last_h = hourly[min(23, len(hourly) - 1)].timestamp

        if rain_24h >= HEAVY_RAIN_CRITICAL_24H_MM:
            return WeatherRiskAssessment(
                alert_type=WeatherAlertType.HEAVY_RAIN,
                severity=WeatherSeverity.CRITICAL,
                risk_score=0.95,
                reasons=[f"Critical Heavy Rainfall: {rain_24h:.1f} mm forecast in next 24 hours (Threshold: {HEAVY_RAIN_CRITICAL_24H_MM} mm)."],
                guidance=[
                    "Extreme waterlogging risk: Clear all perimeter field drains immediately to prevent root hypoxia.",
                    "Halt all foliar chemical applications and granular urea top-dressing."
                ],
                valid_from=first_h,
                valid_until=last_h
            )
        elif rain_24h >= HEAVY_RAIN_WARNING_24H_MM:
            return WeatherRiskAssessment(
                alert_type=WeatherAlertType.HEAVY_RAIN,
                severity=WeatherSeverity.WARNING,
                risk_score=0.75,
                reasons=[f"Heavy Rain Warning: {rain_24h:.1f} mm precipitation forecast over 24 hours (Threshold: {HEAVY_RAIN_WARNING_24H_MM} mm)."],
                guidance=[
                    "Inspect furrow drainage channels to avoid standing water collar rot.",
                    "Suspend chemical spraying; active rain will cause pesticide wash-off."
                ],
                valid_from=first_h,
                valid_until=last_h
            )
        return None

    @staticmethod
    def evaluate_high_humidity_fungal_risk(hourly: List[HourlyForecastPoint]) -> Optional[WeatherRiskAssessment]:
        if not hourly:
            return None
        
        first_h = hourly[0].timestamp
        last_h = hourly[min(23, len(hourly) - 1)].timestamp

        max_continuous = 0
        current_run = 0
        for h in hourly[:24]:
            if h.relative_humidity_percent >= HIGH_HUMIDITY_PERCENT and (FUNGAL_TEMP_MIN_C <= h.temperature_c <= FUNGAL_TEMP_MAX_C):
                current_run += 1
                if current_run > max_continuous:
                    max_continuous = current_run
            else:
                current_run = 0

        if max_continuous >= HIGH_HUMIDITY_MIN_DURATION_HOURS:
            return WeatherRiskAssessment(
                alert_type=WeatherAlertType.HIGH_HUMIDITY,
                severity=WeatherSeverity.ADVISORY,
                risk_score=0.7,
                reasons=[
                    f"Continuous {max_continuous} hours of high humidity (≥{HIGH_HUMIDITY_PERCENT}%) at 18–30°C creates optimal foliar spore germination conditions."
                ],
                guidance=[
                    "Weather conditions are favorable for fungal disease development. Scout lower leaves for Common Rust (Puccinia sorghi) or Blight symptoms.",
                    "Ensure adequate canopy air circulation."
                ],
                valid_from=first_h,
                valid_until=last_h
            )
        return None

    @classmethod
    def generate_alerts(
        cls,
        farm_id: str,
        hourly: List[HourlyForecastPoint],
        source: str = "open-meteo",
        source_status: WeatherSourceStatus = WeatherSourceStatus.LIVE
    ) -> List[WeatherAlertCreate]:
        """
        Synthesizes all biological hazard evaluations into Table 1.6.7 alert payloads.
        Returns a sorted list of alerts (CRITICAL -> WARNING -> ADVISORY -> NORMAL).
        """
        assessments: List[WeatherRiskAssessment] = []

        # 1. Evaluate individual biological risks
        frost_eval = cls.evaluate_frost_risk(hourly)
        if frost_eval:
            assessments.append(frost_eval)

        rain_eval = cls.evaluate_heavy_rain(hourly)
        if rain_eval:
            assessments.append(rain_eval)

        humidity_eval = cls.evaluate_high_humidity_fungal_risk(hourly)
        if humidity_eval:
            assessments.append(humidity_eval)

        # 2. Map assessments to Table 1.6.7 payloads
        alerts: List[WeatherAlertCreate] = []
        now_dt = datetime.now()

        for a in assessments:
            title = f"{a.severity.value} {a.alert_type.value.upper()} ALERT" if a.severity != WeatherSeverity.ADVISORY else f"{a.alert_type.value} Advisory"
            msg = a.reasons[0] if a.reasons else "Atmospheric anomaly detected."
            trigger_val = None
            trigger_unit = None
            threshold_val = None

            if a.alert_type == WeatherAlertType.FROST:
                min_t = min(h.temperature_c for h in hourly[:24]) if hourly else 0.0
                trigger_val = min_t
                trigger_unit = "°C"
                threshold_val = FROST_CRITICAL_C if a.severity == WeatherSeverity.CRITICAL else FROST_ADVISORY_C
            elif a.alert_type == WeatherAlertType.HEAVY_RAIN:
                r_sum = sum(h.rainfall_mm for h in hourly[:24]) if hourly else 0.0
                trigger_val = round(r_sum, 1)
                trigger_unit = "mm"
                threshold_val = HEAVY_RAIN_CRITICAL_24H_MM if a.severity == WeatherSeverity.CRITICAL else HEAVY_RAIN_WARNING_24H_MM
            elif a.alert_type == WeatherAlertType.HIGH_HUMIDITY:
                trigger_val = float(HIGH_HUMIDITY_MIN_DURATION_HOURS)
                trigger_unit = "hours"
                threshold_val = float(HIGH_HUMIDITY_MIN_DURATION_HOURS)

            alerts.append(
                WeatherAlertCreate(
                    farm_id=farm_id,
                    alert_type=a.alert_type,
                    severity=a.severity,
                    alert_date=now_dt,
                    title=title,
                    message=msg,
                    trigger_value=trigger_val,
                    trigger_unit=trigger_unit,
                    threshold_value=threshold_val,
                    guidance=a.guidance,
                    is_active=True,
                    source=source,
                    source_status=source_status,
                    forecast_timestamp=a.valid_from
                )
            )

        # 3. If no hazards, emit Table 1.6.7 NONE record
        if not alerts:
            alerts.append(
                WeatherAlertCreate(
                    farm_id=farm_id,
                    alert_type=WeatherAlertType.NONE,
                    severity=WeatherSeverity.NORMAL,
                    alert_date=now_dt,
                    title="Optimal Atmospheric Conditions",
                    message="Weather parameters are within the safe physiological comfort zone for maize.",
                    trigger_value=None,
                    trigger_unit=None,
                    threshold_value=None,
                    guidance=["Maintain regular crop observation and standard drip irrigation schedules."],
                    is_active=False,
                    source=source,
                    source_status=source_status,
                    forecast_timestamp=now_dt
                )
            )

        # Sort: CRITICAL -> WARNING -> ADVISORY -> NORMAL
        severity_order = {
            WeatherSeverity.CRITICAL: 1,
            WeatherSeverity.WARNING: 2,
            WeatherSeverity.ADVISORY: 3,
            WeatherSeverity.NORMAL: 4
        }
        alerts.sort(key=lambda item: severity_order.get(item.severity, 99))
        return alerts

    @classmethod
    async def generate_alert_id(cls, db: Any = None) -> str:
        """
        Generates a unique 8-character alert_id (format WA000001) adhering to Table 1.6.7 (max 10 chars).
        """
        if db is not None:
            try:
                from pymongo import ReturnDocument
                seq = await db["counters"].find_one_and_update(
                    {"_id": "weather_alert_id"},
                    {"$inc": {"seq": 1}},
                    upsert=True,
                    return_document=ReturnDocument.AFTER
                )
                if seq and "seq" in seq:
                    return f"WA{seq['seq']:06d}"
            except Exception as e:
                logger.warning(f"Error querying sequence counter for alert_id: {e}")
        return f"WA{secrets.token_hex(3).upper()}"

    @classmethod
    async def save_alert(cls, db: Any, alert_data: WeatherAlertCreate) -> WeatherAlertOut:
        """
        Persists a single Table 1.6.7 weather alert document into MongoDB.
        """
        now_dt = datetime.now()
        alert_id = await cls.generate_alert_id(db)

        doc = alert_data.dict()
        doc["alert_id"] = alert_id
        doc["created_at"] = now_dt
        doc["updated_at"] = now_dt

        if db is not None:
            await db["weather_alerts"].insert_one(doc)

        return WeatherAlertOut(**doc)

    @classmethod
    async def sync_and_save_alerts(
        cls,
        db: Any,
        farm_id: str,
        alerts: List[WeatherAlertCreate],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> List[WeatherAlertOut]:
        """
        Persists newly generated biological hazard alerts and dispatches notifications with deduplication.
        """
        from .notification_service import NotificationService
        saved_alerts: List[WeatherAlertOut] = []
        now_dt = datetime.now()

        for alert_create in alerts:
            if alert_create.alert_type == WeatherAlertType.NONE:
                saved_alerts.append(
                    WeatherAlertOut(
                        **alert_create.dict(),
                        alert_id="WA000000",
                        created_at=now_dt,
                        updated_at=now_dt
                    )
                )
                continue

            if db is not None:
                two_hours_ago = now_dt - timedelta(hours=2)
                existing = await db["weather_alerts"].find_one({
                    "farm_id": farm_id,
                    "alert_type": alert_create.alert_type.value,
                    "severity": alert_create.severity.value,
                    "is_active": True,
                    "created_at": {"$gte": two_hours_ago}
                })
                if existing:
                    existing["_id"] = str(existing.get("_id", ""))
                    saved_alerts.append(WeatherAlertOut(**existing))
                    continue

            alert_out = await cls.save_alert(db, alert_create)
            saved_alerts.append(alert_out)

            try:
                await NotificationService.dispatch_weather_alert(db, alert_out, user_profile)
            except Exception as e:
                logger.warning(f"Failed to dispatch notification for alert {alert_out.alert_id}: {e}")

        return saved_alerts

    @classmethod
    async def get_active_alerts_for_farm(cls, db: Any, farm_id: str) -> List[WeatherAlertOut]:
        """
        Retrieves all currently active Table 1.6.7 weather alerts for a farm.
        """
        if db is None:
            return []
        cursor = db["weather_alerts"].find({"farm_id": farm_id, "is_active": True}).sort("created_at", -1)
        docs = await cursor.to_list(length=50)
        return [WeatherAlertOut(**doc) for doc in docs]

    @classmethod
    async def get_all_alerts_for_farm(cls, db: Any, farm_id: str, limit: int = 50) -> List[WeatherAlertOut]:
        """
        Retrieves historical and active alerts for a farm.
        """
        if db is None:
            return []
        cursor = db["weather_alerts"].find({"farm_id": farm_id}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [WeatherAlertOut(**doc) for doc in docs]

    @classmethod
    async def acknowledge_alert(cls, db: Any, alert_id: str) -> bool:
        """
        Acknowledges and deactivates an alert.
        """
        if db is None:
            return True
        res = await db["weather_alerts"].update_one(
            {"alert_id": alert_id},
            {"$set": {"is_active": False, "acknowledged_at": datetime.now(), "updated_at": datetime.now()}}
        )
        return res.modified_count > 0

