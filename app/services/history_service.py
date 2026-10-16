import logging
from datetime import datetime, time
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import settings
from ..schemas import (
    TimelineEntryOut,
    TimelineResponse,
    AdvisoryHistoryEntryOut,
    AdvisoryHistoryResponse
)
from .data_quality_service import DataQualityService

logger = logging.getLogger("agroguard.history_service")

class HistoryService:
    @staticmethod
    def _format_generated_at() -> str:
        tz = DataQualityService.get_timezone()
        return datetime.now(tz).isoformat()

    @staticmethod
    def build_query(
        farm_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Builds a query targeting valid CORN scans for a farm,
        with optional inclusive start and end date filtering.
        """
        query: Dict[str, Any] = {
            "farm_id": farm_id,
            "validation_stage": "CORN"
        }

        date_filters: Dict[str, Any] = {}
        if start_date and start_date.strip():
            try:
                start_dt = datetime.strptime(start_date.strip()[:10], "%Y-%m-%d")
                date_filters["$gte"] = start_dt
            except ValueError:
                pass

        if end_date and end_date.strip():
            try:
                end_dt = datetime.combine(
                    datetime.strptime(end_date.strip()[:10], "%Y-%m-%d").date(),
                    time(23, 59, 59, 999999)
                )
                date_filters["$lte"] = end_dt
            except ValueError:
                pass

        if date_filters:
            query["scan_date"] = date_filters

        return query

    @classmethod
    async def get_all_valid_scans(
        cls,
        farm_id: str,
        db: AsyncIOMotorDatabase,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all valid CORN scans chronologically sorted by scan_date ascending.
        """
        query = cls.build_query(farm_id, start_date, end_date)
        cursor = db["scans"].find(query).sort("scan_date", 1)
        return await cursor.to_list(length=1000)

    @classmethod
    async def get_timeline(
        cls,
        farm_id: str,
        farm: Dict[str, Any],
        db: AsyncIOMotorDatabase,
        page: int = 1,
        page_size: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> TimelineResponse:
        """
        Provides paginated, chronological scan timeline entries with recalculated DAS.
        """
        # Clamp pagination parameters
        max_page_size = settings.MODULE4_TIMELINE_MAX_PAGE_SIZE
        page_size = max(1, min(page_size, max_page_size))
        page = max(1, page)
        skip = (page - 1) * page_size

        query = cls.build_query(farm_id, start_date, end_date)
        total_count = await db["scans"].count_documents(query)

        # Retrieve all scans for data quality evaluation across the query scope
        all_scans_cursor = db["scans"].find(query).sort("scan_date", 1)
        all_scans = await all_scans_cursor.to_list(length=1000)

        sowing_date = farm.get("sowing_date")
        data_quality = DataQualityService.evaluate_quality(all_scans, sowing_date)

        # Retrieve the specific paginated slice
        slice_cursor = db["scans"].find(query).sort("scan_date", 1).skip(skip).limit(page_size)
        page_scans = await slice_cursor.to_list(length=page_size)

        items: List[TimelineEntryOut] = []
        for s in page_scans:
            s_date = s.get("scan_date")
            das = DataQualityService.compute_das(s_date, sowing_date)
            # Fallback to stored day_count only if sowing_date missing
            if das is None and not sowing_date:
                das = s.get("day_count")

            h_info = s.get("height") or {}
            g_info = s.get("growth") or {}
            d_info = s.get("disease_log") or {}
            hlth = s.get("health") or {}
            mod3_adv = s.get("module3_advisory") or {}

            items.append(
                TimelineEntryOut(
                    scan_id=str(s.get("scan_id", "")),
                    scan_date=s_date if isinstance(s_date, datetime) else datetime.utcnow(),
                    day_count=das,
                    growth_week=g_info.get("visual_week") or s.get("growth_stage"),
                    measured_height_cm=h_info.get("measured_height_cm"),
                    height_status=h_info.get("height_status"),
                    disease_status=d_info.get("detected_disease"),
                    disease_confidence=d_info.get("confidence_score"),
                    health_composite=hlth.get("growth_status"),
                    recommendation_status=mod3_adv.get("recommendation_status"),
                    image_url=s.get("image_url")
                )
            )

        return TimelineResponse(
            farm_id=farm_id,
            generated_at=cls._format_generated_at(),
            data_quality=data_quality,
            total_count=total_count,
            page=page,
            page_size=page_size,
            items=items
        )

    @classmethod
    async def get_advisories(
        cls,
        farm_id: str,
        farm: Dict[str, Any],
        db: AsyncIOMotorDatabase
    ) -> AdvisoryHistoryResponse:
        """
        Retrieves all advisories generated across the farm's valid scan history.
        """
        scans = await cls.get_all_valid_scans(farm_id, db)
        sowing_date = farm.get("sowing_date")
        data_quality = DataQualityService.evaluate_quality(scans, sowing_date)

        items: List[AdvisoryHistoryEntryOut] = []

        for s in scans:
            mod3_adv = s.get("module3_advisory") or {}
            dosage = s.get("dosage_details")
            agronomic_text = s.get("agronomic_advisory")

            has_mod3 = bool(mod3_adv)
            if not has_mod3 and not dosage and not agronomic_text:
                continue

            s_date = s.get("scan_date")
            scan_date_str = (
                s_date.strftime("%Y-%m-%d")
                if isinstance(s_date, datetime)
                else str(s_date)[:10] if s_date else ""
            )

            das = DataQualityService.compute_das(s_date, sowing_date)
            if das is None and not sowing_date:
                das = s.get("day_count")

            priority_tier = None
            recommendation_status = None
            stress_hypothesis = None
            farmer_summary = None
            has_chem = False
            has_non_chem = False

            if has_mod3:
                priority_tier = mod3_adv.get("priority_tier")
                recommendation_status = mod3_adv.get("recommendation_status")
                diag = mod3_adv.get("diagnostic") or {}
                stress_hypothesis = diag.get("stress_hypothesis")
                farmer_summary = mod3_adv.get("farmer_summary")
                has_chem = bool(mod3_adv.get("pesticide_treatment") or mod3_adv.get("fertilizer_advisory"))
                has_non_chem = bool(mod3_adv.get("non_chemical_action"))
            else:
                farmer_summary = agronomic_text or dosage
                has_chem = bool(dosage)

            items.append(
                AdvisoryHistoryEntryOut(
                    scan_id=str(s.get("scan_id", "")),
                    scan_date=scan_date_str,
                    das=das,
                    priority_tier=priority_tier,
                    recommendation_status=recommendation_status,
                    stress_hypothesis=stress_hypothesis,
                    farmer_summary=farmer_summary,
                    has_chemical_treatment=has_chem,
                    has_non_chemical_action=has_non_chem
                )
            )

        return AdvisoryHistoryResponse(
            farm_id=farm_id,
            generated_at=cls._format_generated_at(),
            data_quality=data_quality,
            items=items,
            total_advisories=len(items)
        )
