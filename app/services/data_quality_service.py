import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo
from ..config import settings
from ..schemas import DataQualityOut

logger = logging.getLogger("agroguard.data_quality_service")

class DataQualityService:
    @staticmethod
    def get_timezone() -> ZoneInfo:
        try:
            return ZoneInfo(settings.MODULE4_TIMEZONE)
        except Exception:
            return ZoneInfo("Asia/Kolkata")

    @classmethod
    def compute_das(cls, scan_date: Any, farm_sowing_date: Optional[str]) -> Optional[int]:
        """
        Single canonical DAS calculation for Module 4.
        Always recalculates from the current farm.sowing_date.
        """
        if not farm_sowing_date or not str(farm_sowing_date).strip():
            return None

        try:
            sowing = datetime.strptime(str(farm_sowing_date).strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            return None

        if isinstance(scan_date, datetime):
            scan_dt = scan_date.date()
        elif isinstance(scan_date, date):
            scan_dt = scan_date
        elif isinstance(scan_date, str):
            try:
                scan_dt = datetime.strptime(scan_date[:10], "%Y-%m-%d").date()
            except ValueError:
                return None
        else:
            return None

        das = (scan_dt - sowing).days
        if das < 0:
            return None
        return das

    @classmethod
    def evaluate_quality(
        cls,
        scans: List[Dict[str, Any]],
        farm_sowing_date: Optional[str]
    ) -> DataQualityOut:
        """
        Evaluates historical data quality across total scans, valid measurements,
        temporal spacing, and recency under the configured timezone.
        """
        total_scans = len(scans)
        missing_sowing_date = not bool(farm_sowing_date and str(farm_sowing_date).strip())
        das_available = not missing_sowing_date

        if total_scans == 0:
            return DataQualityOut(
                total_scans=0,
                valid_height_scans=0,
                valid_disease_scans=0,
                missing_sowing_date=missing_sowing_date,
                das_available=das_available,
                last_scan_date=None,
                days_since_last_scan=None,
                average_days_between_scans=None,
                longest_gap_days=None,
                quality_level="INSUFFICIENT"
            )

        valid_height_scans = 0
        valid_disease_scans = 0
        scan_dates: List[date] = []

        min_conf = settings.MODULE4_MIN_DISEASE_CONFIDENCE

        for s in scans:
            # 1. Height validity check
            h_info = s.get("height") or {}
            measured_h = h_info.get("measured_height_cm")
            h_status = h_info.get("height_status")
            if measured_h is not None and h_status not in [None, "NO_MARKER", "REJECTED"]:
                valid_height_scans += 1

            # 2. Disease validity check
            d_info = s.get("disease_log") or {}
            conf = float(d_info.get("confidence_score") or 0.0)
            if conf >= min_conf:
                valid_disease_scans += 1

            # 3. Extract scan date
            s_date = s.get("scan_date")
            if isinstance(s_date, datetime):
                scan_dates.append(s_date.date())
            elif isinstance(s_date, str):
                try:
                    scan_dates.append(datetime.strptime(s_date[:10], "%Y-%m-%d").date())
                except ValueError:
                    pass

        scan_dates.sort()

        # Recency & Intervals
        tz = cls.get_timezone()
        today = datetime.now(tz).date()

        last_scan_date_str = None
        days_since_last_scan = None
        average_days_between = None
        longest_gap_days = None

        if scan_dates:
            last_date = scan_dates[-1]
            last_scan_date_str = last_date.isoformat()
            days_since_last_scan = max(0, (today - last_date).days)

            if len(scan_dates) > 1:
                gaps = [(scan_dates[i] - scan_dates[i - 1]).days for i in range(1, len(scan_dates))]
                if gaps:
                    average_days_between = round(sum(gaps) / len(gaps), 1)
                    longest_gap_days = max(gaps)

        # Determine quality level:
        # INSUFFICIENT: < 2 valid scans
        # LIMITED: missing sowing date OR < 50% height coverage OR longest gap > 30 days
        # GOOD: sowing date present, >= 50% height coverage, max gap <= 30 days
        if total_scans < 2:
            quality_level = "INSUFFICIENT"
        elif (
            missing_sowing_date
            or (valid_height_scans < (total_scans * 0.5))
            or (longest_gap_days is not None and longest_gap_days > 30)
        ):
            quality_level = "LIMITED"
        else:
            quality_level = "GOOD"

        return DataQualityOut(
            total_scans=total_scans,
            valid_height_scans=valid_height_scans,
            valid_disease_scans=valid_disease_scans,
            missing_sowing_date=missing_sowing_date,
            das_available=das_available,
            last_scan_date=last_scan_date_str,
            days_since_last_scan=days_since_last_scan,
            average_days_between_scans=average_days_between,
            longest_gap_days=longest_gap_days,
            quality_level=quality_level
        )
