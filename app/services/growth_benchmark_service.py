import logging
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from .multimodal_health_engine import MultimodalHealthEngine, BASE_GROWTH_BENCHMARKS

logger = logging.getLogger("agroguard.growth_benchmark_service")

class GrowthBenchmarkService:
    @staticmethod
    async def get_expected_range(
        das: int,
        variety: str = "GAYMH-1",
        season: str = "KHARIF",
        soil_type: str = "Sandy Loam (Goradu)",
        db: Optional[AsyncIOMotorDatabase] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Determines the biological week and expected height range (min, max in cm)
        for a given DAS, crop variety, season, and soil context.
        Attempts MongoDB collection lookup, falling back to BASE_GROWTH_BENCHMARKS,
        and applies dynamic phenotypic context adjustment.
        """
        if das < 0:
            return None

        week_key = MultimodalHealthEngine.get_stage_for_das(das)

        # 1. Attempt DB lookup if db provided
        db_benchmark = None
        if db is not None:
            try:
                db_benchmark = await db["crop_growth_benchmarks"].find_one({
                    "das_min": {"$lte": das},
                    "das_max": {"$gte": das}
                })
            except Exception as e:
                logger.warning(f"MongoDB benchmark lookup failed: {e}")

        # 2. If DB record found, we can use its week or stage, or fallback to engine
        if db_benchmark:
            target_week = db_benchmark.get("week", week_key)
        else:
            target_week = week_key

        # 3. Compute adjusted range via existing MultimodalHealthEngine
        adjusted = MultimodalHealthEngine.compute_adjusted_height_range(
            week_key=target_week,
            variety=variety,
            season=season,
            soil_type=soil_type
        )

        return {
            "min": adjusted["min"],
            "max": adjusted["max"],
            "range_str": adjusted["range_str"],
            "week": target_week,
            "biological_phase": adjusted.get("biological_phase", ""),
            "phenological_stage": adjusted.get("phenological_stage", "")
        }
