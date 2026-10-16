import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from ..config import settings
from ..schemas import (
    SeasonOverviewResponse,
    SeasonStatisticsResponse
)
from .data_quality_service import DataQualityService

logger = logging.getLogger("agroguard.season_summary_service")

class SeasonSummaryService:
    @staticmethod
    def _format_generated_at() -> str:
        tz = DataQualityService.get_timezone()
        return datetime.now(tz).isoformat()

    @classmethod
    def build_overview(
        cls,
        farm_id: str,
        scans: List[Dict[str, Any]],
        farm: Dict[str, Any]
    ) -> SeasonOverviewResponse:
        """
        Builds a quick-glance current operational state for the dashboard header.
        """
        sowing_date = farm.get("sowing_date")
        data_quality = DataQualityService.evaluate_quality(scans, sowing_date)

        crop_type = farm.get("crop_type", "Corn")
        total_scans = len(scans)

        latest_growth_week = None
        latest_height_cm = None
        latest_height_status = None
        latest_health_status = None
        current_das = None

        if scans:
            latest_scan = scans[-1]
            s_date = latest_scan.get("scan_date")
            current_das = DataQualityService.compute_das(s_date, sowing_date)

            h_info = latest_scan.get("height") or {}
            latest_height_cm = h_info.get("measured_height_cm")
            latest_height_status = h_info.get("height_status")

            g_info = latest_scan.get("growth") or {}
            latest_growth_week = g_info.get("visual_week") or latest_scan.get("growth_stage")

            hlth = latest_scan.get("health") or {}
            latest_health_status = hlth.get("growth_status")

        return SeasonOverviewResponse(
            farm_id=farm_id,
            generated_at=cls._format_generated_at(),
            data_quality=data_quality,
            crop_type=crop_type,
            sowing_date=sowing_date,
            das_available=data_quality.das_available,
            current_das=current_das,
            total_scans=total_scans,
            latest_growth_week=latest_growth_week,
            latest_height_cm=latest_height_cm,
            latest_height_status=latest_height_status,
            latest_health_status=latest_health_status
        )

    @classmethod
    def build_statistics(
        cls,
        farm_id: str,
        scans: List[Dict[str, Any]],
        farm: Dict[str, Any]
    ) -> SeasonStatisticsResponse:
        """
        Assembles comprehensive descriptive lifecycle metrics across growth,
        pathology, advisories, and scan interval consistency.
        """
        sowing_date = farm.get("sowing_date")
        data_quality = DataQualityService.evaluate_quality(scans, sowing_date)

        crop_type = farm.get("crop_type", "Corn")
        total_scans = len(scans)

        lifecycle_days = None
        if len(scans) >= 2:
            first_date = scans[0].get("scan_date")
            last_date = scans[-1].get("scan_date")

            def to_d(dt_val):
                if isinstance(dt_val, datetime):
                    return dt_val.date()
                if isinstance(dt_val, str):
                    try:
                        return datetime.strptime(dt_val[:10], "%Y-%m-%d").date()
                    except ValueError:
                        return None
                return None

            d1 = to_d(first_date)
            d2 = to_d(last_date)
            if d1 and d2:
                lifecycle_days = max(0, (d2 - d1).days)

        # Growth score
        valid_height_scans = 0
        within_expected_scans = 0
        latest_growth_status = None
        latest_health_status = None

        min_conf = settings.MODULE4_MIN_DISEASE_CONFIDENCE
        no_disease = set(
            lbl.strip()
            for lbl in settings.MODULE4_NO_DISEASE_LABELS.split(",")
            if lbl.strip()
        )

        disease_incidents = 0
        unique_diseases_set = set()

        total_advisories = 0
        chemical_advisories = 0
        non_chemical_advisories = 0

        for s in scans:
            # 1. Height metrics
            h_info = s.get("height") or {}
            measured_h = h_info.get("measured_height_cm")
            h_status = h_info.get("height_status")
            if measured_h is not None and h_status not in [None, "NO_MARKER", "REJECTED"]:
                valid_height_scans += 1
                if h_status == "WITHIN_EXPECTED":
                    within_expected_scans += 1

            # 2. Disease metrics
            d_info = s.get("disease_log") or {}
            disease = d_info.get("detected_disease")
            conf = float(d_info.get("confidence_score", 0.0) or 0.0)
            if disease and (disease not in no_disease) and conf >= min_conf:
                disease_incidents += 1
                unique_diseases_set.add(disease)

            # 3. Advisory metrics from Module 3 or legacy advisory
            mod3_adv = s.get("module3_advisory") or {}
            if mod3_adv:
                total_advisories += 1
                has_chem = bool(mod3_adv.get("pesticide_treatment") or mod3_adv.get("fertilizer_advisory"))
                has_non_chem = bool(mod3_adv.get("non_chemical_action"))
                if has_chem:
                    chemical_advisories += 1
                if has_non_chem:
                    non_chemical_advisories += 1
            elif s.get("dosage_details") or s.get("agronomic_advisory"):
                total_advisories += 1
                chemical_advisories += 1

        if valid_height_scans > 0:
            growth_score_percent = round((within_expected_scans / valid_height_scans) * 100.0, 1)
            growth_score_available = True
        else:
            growth_score_percent = None
            growth_score_available = False

        if scans:
            latest_scan = scans[-1]
            h_info = latest_scan.get("height") or {}
            latest_growth_status = h_info.get("height_status")

            hlth = latest_scan.get("health") or {}
            latest_health_status = hlth.get("growth_status")

        return SeasonStatisticsResponse(
            farm_id=farm_id,
            generated_at=cls._format_generated_at(),
            data_quality=data_quality,
            crop_type=crop_type,
            sowing_date=sowing_date,
            total_scans=total_scans,
            lifecycle_days=lifecycle_days,
            growth_score_percent=growth_score_percent,
            growth_score_available=growth_score_available,
            valid_height_scans=valid_height_scans,
            within_expected_scans=within_expected_scans,
            latest_growth_status=latest_growth_status,
            latest_health_status=latest_health_status,
            disease_incidents=disease_incidents,
            unique_diseases=sorted(list(unique_diseases_set)),
            total_advisories=total_advisories,
            chemical_advisories=chemical_advisories,
            non_chemical_advisories=non_chemical_advisories,
            average_days_between_scans=data_quality.average_days_between_scans,
            longest_gap_days=data_quality.longest_gap_days
        )
