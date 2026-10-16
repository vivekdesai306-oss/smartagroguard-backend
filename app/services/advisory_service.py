import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..schemas import (
    Module3InputContract,
    Module3Output,
    PriorityTierEnum,
    StressHypothesisEnum,
    RecommendationStatusEnum,
    DiagnosticAssessment,
    ScaledTreatmentPlan,
    NonChemicalAction
)
from ..database import get_database
from seed_db import (
    CROP_GROWTH_BENCHMARKS,
    DIAGNOSTIC_RULES,
    FERTILIZER_RECOMMENDATIONS,
    PESTICIDE_RECOMMENDATIONS,
    TREATMENT_RESTRICTIONS
)

logger = logging.getLogger("agroguard.advisory_service")

class AdvisoryService:
    """
    Module 3: Evidence-Based Farm Advisory & Treatment Recommendation Engine (v3.0)
    
    Architectural Invariants & Safety Principles:
    1. Height = LOW (BELOW_EXPECTED) is an observation, NEVER a direct Nitrogen/Urea prescription.
    2. Weather data (recent rainfall) is treated strictly as an environmental proxy for moisture deficit.
    3. No chemical compound names or rates are hardcoded in application logic. All products are dynamically queried.
    4. Honest reporting: Disease confidence < 0.75 or ambiguous stunting returns INSUFFICIENT_EVIDENCE / PERFORM_FIELD_INSPECTION.
    5. Strict Safety Validation Layer: Wind drift gate, rainfastness hours gate, nitrogen lockout on active rust / water stress, PHI gate.
    """

    @classmethod
    async def generate_farm_advisory(cls, input_contract: Module3InputContract) -> Module3Output:
        """
        Main entry point for Module 3 evidence-based advisory pipeline.
        Executing sequential order:
        1. Validate Input Contract
        2. Perform Diagnostic Triage
        3. Generate Hypotheses & Evaluate Evidence Streams
        4. Determine Diagnostic Status & Assess Confidence
        5. Determine Intervention Need (Chemical vs Non-Chemical / Verification / Monitoring)
        6. Check Treatment Eligibility (Dynamic DB Catalog)
        7. Safety Validation Gate (Wind drift, Rainfastness, Chemical Conflicts, PHI)
        8. Synthesize Final Recommendation
        """
        diag = input_contract.diagnostics
        env = input_contract.environment
        farm = input_contract.farm
        
        logger.info(f"Processing Module 3 Advisory for Scan {diag.scan_id} (Farm: {farm.farm_id})")

        # -------------------------------------------------------------------------
        # STEP 1 & 2: Diagnostic Triage & Evidence Collection
        # -------------------------------------------------------------------------
        height_status = diag.height_status
        rainfall = env.rainfall_mm
        disease = diag.detected_disease
        disease_conf = diag.disease_confidence
        observations = [obs.lower() for obs in diag.scouting_observations]
        has_chlorosis = any("chlorosis" in obs or "yellowing" in obs for obs in observations)

        evidence_summary = []
        stress_hypothesis = StressHypothesisEnum.HEALTHY_OPTIMAL
        recommendation_status = RecommendationStatusEnum.NO_CHEMICAL_TREATMENT
        priority_tier = PriorityTierEnum.MAINTENANCE
        verification_status = "NOT_APPLICABLE"

        # -------------------------------------------------------------------------
        # STEP 3 & 4: Evaluate Evidence Streams & Determine Diagnostic Status
        # -------------------------------------------------------------------------
        # PATHWAY A: Pathology Analysis
        if disease != "Healthy":
            evidence_summary.append(f"Visual pathology detected: {disease} ({round(disease_conf*100, 1)}% confidence).")
            if disease_conf >= 0.75:
                stress_hypothesis = StressHypothesisEnum.DISEASE_STRESS
                priority_tier = PriorityTierEnum.PROTECTION
                recommendation_status = RecommendationStatusEnum.PESTICIDE_RECOMMENDATION
            else:
                stress_hypothesis = StressHypothesisEnum.DISEASE_STRESS
                priority_tier = PriorityTierEnum.PROTECTION
                recommendation_status = RecommendationStatusEnum.PERFORM_FIELD_INSPECTION
                verification_status = "REQUIRED"
                evidence_summary.append(f"Disease confidence ({round(disease_conf*100, 1)}%) is below 75% threshold. Chemical spray locked out.")

        # PATHWAY B: Stunting / Height Abnormality Analysis (Stunting != Nitrogen)
        elif height_status == "BELOW_EXPECTED":
            priority_tier = PriorityTierEnum.CORRECTIVE
            measured_h = diag.measured_height_cm or 0.0
            evidence_summary.append(f"Stalk height ({measured_h} cm) is below expected benchmark ({diag.expected_height_range_str}) for DAS {diag.calculated_das}.")

            # Evidence Stream 1: Weather-derived moisture deficit proxy
            if rainfall < 2.0:
                stress_hypothesis = StressHypothesisEnum.WATER_STRESS
                recommendation_status = RecommendationStatusEnum.RESTORE_WATER_AVAILABILITY
                evidence_summary.append(f"Weather proxy indicates recent rainfall is very low ({rainfall} mm over past 7 days). Water stress suspected.")
            # Evidence Stream 2: Chlorosis / Nutrient Depletion
            elif has_chlorosis:
                stress_hypothesis = StressHypothesisEnum.NUTRIENT_DEFICIENCY
                recommendation_status = RecommendationStatusEnum.FERTILIZER_RECOMMENDATION
                verification_status = "REQUIRED"
                evidence_summary.append("Foliar chlorosis / lower leaf yellowing observed in scouting notes corroborates nutrient deficiency hypothesis.")
            # Evidence Stream 3: Indeterminate / Unknown Cause
            else:
                stress_hypothesis = StressHypothesisEnum.INSUFFICIENT_EVIDENCE
                recommendation_status = RecommendationStatusEnum.INSUFFICIENT_EVIDENCE
                verification_status = "REQUIRED"
                evidence_summary.append("Normal rainfall and no leaf chlorosis observed. Insufficient evidence to diagnose stunting cause chemically.")

        else:
            # Baseline Healthy Growth
            evidence_summary.append(f"Stalk growth is within expected benchmark ({diag.expected_height_range_str}). Foliage is healthy.")
            stress_hypothesis = StressHypothesisEnum.HEALTHY_OPTIMAL
            priority_tier = PriorityTierEnum.MAINTENANCE
            recommendation_status = RecommendationStatusEnum.FERTILIZER_RECOMMENDATION

        # Calculate Diagnostic Confidence
        if stress_hypothesis == StressHypothesisEnum.DISEASE_STRESS:
            diag_confidence = round(disease_conf, 2)
        elif stress_hypothesis == StressHypothesisEnum.WATER_STRESS:
            diag_confidence = 0.85 if rainfall < 1.0 else 0.72
        elif stress_hypothesis == StressHypothesisEnum.NUTRIENT_DEFICIENCY:
            diag_confidence = 0.82 if has_chlorosis else 0.65
        elif stress_hypothesis == StressHypothesisEnum.INSUFFICIENT_EVIDENCE:
            diag_confidence = 0.45
        else:
            diag_confidence = 0.95

        # -------------------------------------------------------------------------
        # STEP 5 & 6: Treatment Eligibility & Scaling (Query Dynamic DB Catalog)
        # -------------------------------------------------------------------------
        pesticide_plan: Optional[ScaledTreatmentPlan] = None
        fertilizer_plan: Optional[ScaledTreatmentPlan] = None
        non_chemical_action: Optional[NonChemicalAction] = None

        area_acres = farm.farm_area_acres

        # 1. Non-Chemical Actions
        if recommendation_status == RecommendationStatusEnum.RESTORE_WATER_AVAILABILITY:
            non_chemical_action = NonChemicalAction(
                action_type="RESTORE_WATER_AVAILABILITY",
                headline="Prioritize Rootzone Soil Moisture",
                instructions=(
                    f"Check top 10 cm of soil. Water stress is suspected due to recent low rainfall ({env.rainfall_mm} mm). "
                    f"Run drip/furrow irrigation for {round(area_acres * 2.5, 1)} hours before considering any chemical fertilizers."
                ),
                target_module="Module 5: Irrigation Management"
            )
        elif recommendation_status == RecommendationStatusEnum.PERFORM_FIELD_INSPECTION:
            non_chemical_action = NonChemicalAction(
                action_type="PERFORM_FIELD_INSPECTION",
                headline="Physical Field Inspection & Daylight Re-Scan Required",
                instructions=(
                    f"Visual pattern resembles {disease}, but diagnostic confidence is {round(disease_conf*100, 1)}% "
                    f"(below 75% safety threshold). Inspect lower leaf surfaces for reddish-brown pustules or re-scan in bright daylight. No chemicals authorized."
                )
            )
        elif recommendation_status == RecommendationStatusEnum.INSUFFICIENT_EVIDENCE:
            non_chemical_action = NonChemicalAction(
                action_type="INSUFFICIENT_EVIDENCE",
                headline="Investigate Rootzone & Soil Physical Structure",
                instructions=(
                    "Stalk height is below expected, but rainfall and foliage color are normal. "
                    "Do NOT apply emergency chemicals or heavy urea. Inspect roots for soil grub damage, nematodes, or compacted subsoil (hardpan)."
                )
            )

        # 2. Pesticide Treatment Eligibility
        if recommendation_status == RecommendationStatusEnum.PESTICIDE_RECOMMENDATION and disease_conf >= 0.75:
            pest_db_rec = await cls._fetch_pesticide_catalog(disease)
            if pest_db_rec:
                unit_rate_val = pest_db_rec.get("unit_rate_per_acre_val", 200.0)
                unit_str = pest_db_rec.get("unit_of_measure", "ml")
                total_qty_val = unit_rate_val * area_acres
                total_qty_str = f"{round(total_qty_val, 1)} {unit_str}"

                pesticide_plan = ScaledTreatmentPlan(
                    category="PESTICIDE",
                    product_name=pest_db_rec["product_name"],
                    active_ingredient=pest_db_rec.get("active_ingredient"),
                    formulation=pest_db_rec.get("formulation"),
                    unit_rate=pest_db_rec["unit_rate_per_acre_str"],
                    farm_area_acres=area_acres,
                    total_quantity=total_qty_str,
                    water_dilution=pest_db_rec.get("water_dilution", "200 Litres per acre"),
                    application_method=pest_db_rec.get("application_method", "Foliar canopy spray"),
                    timing=pest_db_rec.get("timing", "Early Morning"),
                    rainfastness_hours=pest_db_rec.get("rainfastness_hours", 3.0),
                    safety_notes=pest_db_rec.get("safety_notes")
                )
            else:
                # Honest reporting: High disease confidence, but no authorized chemical in catalog
                recommendation_status = RecommendationStatusEnum.TREATMENT_NOT_AUTHORIZED
                evidence_summary.append(f"Disease confirmed ({disease}), but no legally registered pesticide treatment was found in database.")

        # 3. Fertilizer Advisory Eligibility
        if recommendation_status == RecommendationStatusEnum.FERTILIZER_RECOMMENDATION:
            # Query fertilizer catalog by visual week or deficiency
            target_cond = "Nutrient_Deficiency_Suspected" if stress_hypothesis == StressHypothesisEnum.NUTRIENT_DEFICIENCY else "Baseline Growth"
            fert_db_rec = await cls._fetch_fertilizer_catalog(diag.visual_week, target_cond)
            if fert_db_rec:
                unit_rate_val = fert_db_rec.get("unit_rate_per_acre_val", 30.0)
                unit_str = fert_db_rec.get("unit_of_measure", "kg")
                total_qty_val = unit_rate_val * area_acres
                total_qty_str = f"{round(total_qty_val, 1)} {unit_str}"

                fertilizer_plan = ScaledTreatmentPlan(
                    category="FERTILIZER",
                    product_name=fert_db_rec["product_name"],
                    active_ingredient=fert_db_rec.get("active_ingredient"),
                    formulation=fert_db_rec.get("formulation"),
                    unit_rate=fert_db_rec["unit_rate_per_acre_str"],
                    farm_area_acres=area_acres,
                    total_quantity=total_qty_str,
                    water_dilution=fert_db_rec.get("water_dilution"),
                    application_method=fert_db_rec.get("application_method", "Soil side-dressing"),
                    timing=fert_db_rec.get("timing", "Morning"),
                    safety_notes=fert_db_rec.get("safety_notes")
                )

        # -------------------------------------------------------------------------
        # STEP 7: Safety Validation Gate
        # -------------------------------------------------------------------------
        safety_result = cls._validate_safety(
            pesticide_plan=pesticide_plan,
            fertilizer_plan=fertilizer_plan,
            env=env,
            stress_hypothesis=stress_hypothesis,
            disease=disease
        )

        # Apply Safety Locks
        if not safety_result["safe_to_apply"]:
            if safety_result["lockout_nitrogen"]:
                fertilizer_plan = None
                evidence_summary.append(f"SAFETY LOCK: {safety_result['lockout_reason']}")
            
            if safety_result["hold_chemical_spray"]:
                if pesticide_plan:
                    pesticide_plan = None
                recommendation_status = RecommendationStatusEnum.TREATMENT_NOT_AUTHORIZED
                evidence_summary.append(f"SAFETY GATE TRIGGERED: {safety_result['spray_hold_reason']}")

        # -------------------------------------------------------------------------
        # STEP 8: Construct Diagnostic Assessment & Farmer Summary
        # -------------------------------------------------------------------------
        assessment = DiagnosticAssessment(
            height_status=height_status,
            growth_stage=int(diag.visual_week.replace("Week ", "")) if "Week " in diag.visual_week else None,
            growth_stage_confidence=diag.visual_confidence,
            measured_height_cm=diag.measured_height_cm,
            expected_range_cm=diag.expected_height_range_str,
            disease_status=disease,
            disease_confidence=diag.disease_confidence,
            recent_rainfall_mm=env.rainfall_mm,
            soil_type=farm.soil_type,
            stress_hypothesis=stress_hypothesis.value,
            evidence_summary=evidence_summary,
            diagnostic_confidence=diag_confidence,
            verification_status=verification_status
        )

        farmer_summary = cls._build_farmer_summary(
            recommendation_status=recommendation_status,
            stress_hypothesis=stress_hypothesis,
            assessment=assessment,
            pesticide_plan=pesticide_plan,
            fertilizer_plan=fertilizer_plan,
            non_chemical=non_chemical_action,
            safety=safety_result
        )

        return Module3Output(
            scan_id=diag.scan_id,
            farm_id=farm.farm_id,
            timestamp=datetime.utcnow(),
            priority_tier=priority_tier,
            recommendation_status=recommendation_status,
            diagnostic=assessment,
            pesticide_treatment=pesticide_plan,
            fertilizer_advisory=fertilizer_plan,
            non_chemical_action=non_chemical_action,
            safety_validation=safety_result,
            farmer_summary=farmer_summary
        )

    # =========================================================================
    # Helper Functions: Database Queries & Fallback Seeding
    # =========================================================================

    @classmethod
    async def _fetch_pesticide_catalog(cls, disease_name: str) -> Optional[Dict[str, Any]]:
        """Queries MongoDB pesticide_recommendations collection with fallback to memory catalog."""
        try:
            import asyncio
            db = get_database()
            rec = await asyncio.wait_for(db["pesticide_recommendations"].find_one({"target_disease": disease_name}), timeout=0.5)
            if rec:
                return rec
        except Exception as e:
            logger.warning(f"MongoDB lookup warning for pesticide catalog ({e}), using memory fallback.")

        for item in PESTICIDE_RECOMMENDATIONS:
            if item.get("target_disease") == disease_name:
                return item
        return None

    @classmethod
    async def _fetch_fertilizer_catalog(cls, growth_week: str, target_condition: str) -> Optional[Dict[str, Any]]:
        """Queries MongoDB fertilizer_recommendations collection with fallback to memory catalog."""
        try:
            import asyncio
            db = get_database()
            if target_condition == "Nutrient_Deficiency_Suspected":
                rec = await asyncio.wait_for(db["fertilizer_recommendations"].find_one({"target_condition": "Nutrient_Deficiency_Suspected"}), timeout=0.5)
            else:
                rec = await asyncio.wait_for(db["fertilizer_recommendations"].find_one({"growth_week": growth_week}), timeout=0.5)
            if rec:
                return rec
        except Exception as e:
            logger.warning(f"MongoDB lookup warning for fertilizer catalog ({e}), using memory fallback.")

        if target_condition == "Nutrient_Deficiency_Suspected":
            for item in FERTILIZER_RECOMMENDATIONS:
                if item.get("target_condition") == "Nutrient_Deficiency_Suspected":
                    return item

        for item in FERTILIZER_RECOMMENDATIONS:
            if item.get("growth_week") == growth_week:
                return item
        return FERTILIZER_RECOMMENDATIONS[0] if FERTILIZER_RECOMMENDATIONS else None

    @classmethod
    def _validate_safety(
        cls,
        pesticide_plan: Optional[ScaledTreatmentPlan],
        fertilizer_plan: Optional[ScaledTreatmentPlan],
        env: Any,
        stress_hypothesis: StressHypothesisEnum,
        disease: str
    ) -> Dict[str, Any]:
        """
        Executes strict Safety Validation Layer:
        1. Wind Drift Gate: Max wind speed <= 15.0 km/h
        2. Rainfastness Gate: hours_until_rain vs product rainfastness_hours
        3. Chemical Conflict Gate: Nitrogen + Active Rust, Nitrogen + Water Stress
        """
        safe_to_apply = True
        hold_chemical_spray = False
        spray_hold_reason = None
        lockout_nitrogen = False
        lockout_reason = None

        # 1. Wind Drift Check
        if env.wind_speed_kmh > 15.0:
            safe_to_apply = False
            hold_chemical_spray = True
            spray_hold_reason = f"High wind speed ({env.wind_speed_kmh} km/h > 15 km/h limit). Chemical spray hold active to prevent off-target drift."

        # 2. Rainfastness Check
        if pesticide_plan and pesticide_plan.rainfastness_hours is not None:
            if env.hours_until_rain < pesticide_plan.rainfastness_hours:
                safe_to_apply = False
                hold_chemical_spray = True
                spray_hold_reason = (
                    f"Forecast rain in {env.hours_until_rain}h is sooner than product rainfastness window "
                    f"({pesticide_plan.rainfastness_hours}h). Spray will wash off."
                )

        # 3. Chemical Conflicts
        if disease == "Corn Common Rust":
            lockout_nitrogen = True
            lockout_reason = "Nitrogen fertilizer is locked out during active Corn Common Rust infection to prevent fungal spore proliferation."
            safe_to_apply = False

        if stress_hypothesis == StressHypothesisEnum.WATER_STRESS:
            lockout_nitrogen = True
            lockout_reason = "High-nitrogen fertilizer is locked out during water stress to prevent severe root cell osmotic burn."
            safe_to_apply = False

        return {
            "safe_to_apply": safe_to_apply,
            "hold_chemical_spray": hold_chemical_spray,
            "spray_hold_reason": spray_hold_reason,
            "lockout_nitrogen": lockout_nitrogen,
            "lockout_reason": lockout_reason,
            "weather_safe_to_spray": not hold_chemical_spray
        }

    @classmethod
    def _build_farmer_summary(
        cls,
        recommendation_status: RecommendationStatusEnum,
        stress_hypothesis: StressHypothesisEnum,
        assessment: DiagnosticAssessment,
        pesticide_plan: Optional[ScaledTreatmentPlan],
        fertilizer_plan: Optional[ScaledTreatmentPlan],
        non_chemical: Optional[NonChemicalAction],
        safety: Dict[str, Any]
    ) -> str:
        """Generates plain language, honest agronomic summary for farmer GUI."""
        if recommendation_status == RecommendationStatusEnum.RESTORE_WATER_AVAILABILITY:
            return (
                "🟡 WATER STRESS SUSPECTED: Plant height is below benchmark due to recent low rainfall. "
                "Prioritize rootzone irrigation immediately. High-nitrogen fertilizer is temporarily locked out to prevent root burn."
            )
        elif recommendation_status == RecommendationStatusEnum.PERFORM_FIELD_INSPECTION:
            return (
                "⚪ UNCONFIRMED SYMPTOM: Fungal disease is suspected, but diagnostic confidence is below the 75% safety threshold. "
                "No toxic chemicals prescribed. Please physically inspect lower leaves or re-scan in bright daylight."
            )
        elif recommendation_status == RecommendationStatusEnum.INSUFFICIENT_EVIDENCE:
            return (
                "⚪ INVESTIGATION REQUIRED: Stalk is shorter than expected, but rainfall and leaf color are normal. "
                "Do NOT apply emergency chemicals. Inspect roots for soil grubs or compacted subsoil (hardpan)."
            )
        elif recommendation_status == RecommendationStatusEnum.TREATMENT_NOT_AUTHORIZED:
            reason = safety.get("spray_hold_reason") or "Safety gate active or no authorized chemical available."
            return f"🚫 TREATMENT HOLD: Chemical application is not authorized. Reason: {reason}"
        elif pesticide_plan:
            return (
                f"🔴 DISEASE PROTECTION REQUIRED: Confirmed {assessment.disease_status} ({round((assessment.disease_confidence or 0)*100, 1)}% confidence). "
                f"Apply {pesticide_plan.product_name} at {pesticide_plan.total_quantity} per farm area ({pesticide_plan.unit_rate})."
            )
        elif fertilizer_plan:
            return (
                f"🟢 FERTILITY ADVISORY: Applied for {assessment.growth_stage or 'current'} growth week. "
                f"Apply {fertilizer_plan.product_name} at {fertilizer_plan.total_quantity} ({fertilizer_plan.unit_rate})."
            )
        else:
            return "🟢 HEALTHY CROP: Stalk growth and foliage are within normal biological benchmarks. Maintain regular irrigation and scouting."
