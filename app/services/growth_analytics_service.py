import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import settings
from ..schemas import (
    GrowthCurvePointOut,
    GrowthCurveResponse,
    HealthTrendPointOut,
    HealthTrendResponse
)
from .data_quality_service import DataQualityService
from .growth_benchmark_service import GrowthBenchmarkService

logger = logging.getLogger("agroguard.growth_analytics_service")

class GrowthAnalyticsService:
    @staticmethod
    def _format_generated_at() -> str:
        tz = DataQualityService.get_timezone()
        return datetime.now(tz).isoformat()

    @classmethod
    async def build_growth_curve(
        cls,
        farm_id: str,
        scans: List[Dict[str, Any]],
        farm: Dict[str, Any],
        db: Optional[AsyncIOMotorDatabase] = None
    ) -> GrowthCurveResponse:
        """
        Builds the chronological growth trajectory comparing measured stalk height
        against contextual expected benchmark bands.
        """
        sowing_date = farm.get("sowing_date")
        variety = farm.get("variety", "GAYMH-1")
        season = farm.get("season", "KHARIF")
        soil_type = farm.get("soil_type", "Sandy Loam (Goradu)")

        data_quality = DataQualityService.evaluate_quality(scans, sowing_date)

        points: List[GrowthCurvePointOut] = []
        valid_height_scans = 0
        within_expected_scans = 0

        for s in scans:
            s_date = s.get("scan_date")
            scan_date_str = (
                s_date.strftime("%Y-%m-%d")
                if isinstance(s_date, datetime)
                else str(s_date)[:10] if s_date else ""
            )

            das = DataQualityService.compute_das(s_date, sowing_date)

            h_info = s.get("height") or {}
            measured_h = h_info.get("measured_height_cm")
            h_status = h_info.get("height_status")

            expected_min = None
            expected_max = None
            growth_week = None

            if das is not None:
                bench = await GrowthBenchmarkService.get_expected_range(
                    das=das,
                    variety=variety,
                    season=season,
                    soil_type=soil_type,
                    db=db
                )
                if bench:
                    expected_min = bench.get("min")
                    expected_max = bench.get("max")
                    growth_week = bench.get("week")

            # Score accounting: only valid measured height counts
            if measured_h is not None and h_status not in [None, "NO_MARKER", "REJECTED"]:
                valid_height_scans += 1
                if h_status == "WITHIN_EXPECTED":
                    within_expected_scans += 1

            points.append(
                GrowthCurvePointOut(
                    das=das,
                    scan_date=scan_date_str,
                    measured_height_cm=measured_h,
                    expected_min_cm=expected_min,
                    expected_max_cm=expected_max,
                    height_status=h_status,
                    growth_week=growth_week
                )
            )

        if valid_height_scans > 0:
            growth_score_percent = round((within_expected_scans / valid_height_scans) * 100.0, 1)
            growth_score_available = True
        else:
            growth_score_percent = None
            growth_score_available = False

        return GrowthCurveResponse(
            farm_id=farm_id,
            generated_at=cls._format_generated_at(),
            data_quality=data_quality,
            das_available=data_quality.das_available,
            sowing_date=sowing_date,
            points=points,
            growth_score_percent=growth_score_percent,
            growth_score_available=growth_score_available,
            valid_height_scans=valid_height_scans,
            within_expected_scans=within_expected_scans
        )

    @classmethod
    async def build_health_trend(
        cls,
        farm_id: str,
        scans: List[Dict[str, Any]],
        farm: Dict[str, Any]
    ) -> HealthTrendResponse:
        """
        Builds the chronological disease and composite health timeline across scans.
        """
        sowing_date = farm.get("sowing_date")
        data_quality = DataQualityService.evaluate_quality(scans, sowing_date)

        points: List[HealthTrendPointOut] = []

        for s in scans:
            s_date = s.get("scan_date")
            scan_date_str = (
                s_date.strftime("%Y-%m-%d")
                if isinstance(s_date, datetime)
                else str(s_date)[:10] if s_date else ""
            )

            das = DataQualityService.compute_das(s_date, sowing_date)

            health_info = s.get("health") or {}
            health_status = health_info.get("growth_status", "UNKNOWN")

            d_info = s.get("disease_log") or {}
            disease = d_info.get("detected_disease")
            confidence = d_info.get("confidence_score")

            points.append(
                HealthTrendPointOut(
                    scan_date=scan_date_str,
                    das=das,
                    health_status=health_status,
                    disease=disease,
                    disease_confidence=confidence
                )
            )

        return HealthTrendResponse(
            farm_id=farm_id,
            generated_at=cls._format_generated_at(),
            data_quality=data_quality,
            points=points
        )
