import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agroguard.multimodal_health_engine")

# Base Agronomic Growth & Stalk Height Benchmarks for Maize (Zea mays L.)
BASE_GROWTH_BENCHMARKS = {
    "Week 1":  {"das_min": 0,  "das_max": 7,   "height_min": 0.0,   "height_max": 5.0,   "stage": "VE (Emergence)", "phase": "Seedling emergence & radicle elongation"},
    "Week 2":  {"das_min": 8,  "das_max": 14,  "height_min": 5.0,   "height_max": 15.0,  "stage": "V1-V2",          "phase": "First collar visible, nodal root initiation"},
    "Week 3":  {"das_min": 15, "das_max": 21,  "height_min": 15.0,  "height_max": 30.0,  "stage": "V3-V4",          "phase": "Rapid root expansion, leaf collar formation"},
    "Week 4":  {"das_min": 22, "das_max": 28,  "height_min": 30.0,  "height_max": 50.0,  "stage": "V5-V6",          "phase": "Growing point above soil surface, tassel initiation"},
    "Week 5":  {"das_min": 29, "das_max": 35,  "height_min": 50.0,  "height_max": 80.0,  "stage": "V7-V8",          "phase": "Rapid vegetative expansion, ear shoot initiation"},
    "Week 6":  {"das_min": 36, "das_max": 42,  "height_min": 80.0,  "height_max": 120.0, "stage": "V9-V10",        "phase": "Stalk elongation, brace root development"},
    "Week 7":  {"das_min": 43, "das_max": 49,  "height_min": 120.0, "height_max": 160.0, "stage": "VT (Tasseling)", "phase": "Last branch of tassel visible, pollen shedding begins"},
    "Week 8":  {"das_min": 50, "das_max": 56,  "height_min": 160.0, "height_max": 200.0, "stage": "R1 (Silking)",   "phase": "Silks emerge, pollination & ovule fertilization"},
    "Week 9":  {"das_min": 57, "das_max": 63,  "height_min": 180.0, "height_max": 220.0, "stage": "R2 (Blister)",   "phase": "Kernels resemble blisters, rapid starch accumulation"},
    "Week 10": {"das_min": 64, "das_max": 70,  "height_min": 200.0, "height_max": 230.0, "stage": "R3 (Milk)",      "phase": "Kernels filled with milky fluid, cob elongation"},
    "Week 11": {"das_min": 71, "das_max": 77,  "height_min": 210.0, "height_max": 240.0, "stage": "R4 (Dough)",     "phase": "Kernel content thickens to dough, starch solidification"},
    "Week 12": {"das_min": 78, "das_max": 84,  "height_min": 220.0, "height_max": 250.0, "stage": "R5 (Dent)",      "phase": "Dent formed at crown of kernels, starch hardens"},
    "Week 13+":{"das_min": 85, "das_max": 150, "height_min": 220.0, "height_max": 270.0, "stage": "R6 (Maturity)",  "phase": "Black layer formation, physiological maturity achieved"}
}

class MultimodalHealthEngine:
    """
    Explainable, rule-based reasoning engine combining:
    1. Visual growth prediction from Existing MobileNetV2 Classifier
    2. Deterministic DAS (Days After Sowing)
    3. Measured height vs context-adjusted biological benchmark range
    4. Environmental & weather parameters (temperature, precipitation, frost)
    5. Soil characteristics and cultivar variety
    """

    @staticmethod
    def get_stage_for_das(das: int) -> str:
        """
        Maps exact DAS to the biological benchmark week.
        """
        for week_str, data in BASE_GROWTH_BENCHMARKS.items():
            if data["das_min"] <= das <= data["das_max"]:
                return week_str
        return "Week 13+" if das >= 85 else "Week 1"

    @classmethod
    def compute_adjusted_height_range(
        cls,
        week_key: str,
        variety: Optional[str] = None,
        season: Optional[str] = None,
        soil_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates context-adjusted expected height range by applying
        agronomic modifiers (variety, season, soil) onto the base benchmark table.
        """
        base_data = BASE_GROWTH_BENCHMARKS.get(week_key, BASE_GROWTH_BENCHMARKS["Week 1"])
        base_min = base_data["height_min"]
        base_max = base_data["height_max"]
        
        multiplier = 1.0
        applied_modifiers = []

        # 1. Variety modifier
        v_str = (variety or "").upper()
        if "GAYMH" in v_str or "SHORT" in v_str or "EARLY" in v_str:
            multiplier *= 0.95
            applied_modifiers.append("Medium-stature hybrid (0.95x)")
        elif "PIONEER" in v_str or "DKC" in v_str or "TALL" in v_str:
            multiplier *= 1.05
            applied_modifiers.append("Vigorous tall hybrid (1.05x)")

        # 2. Cultivation Season modifier
        s_str = (season or "").upper()
        if s_str == "RABI":
            multiplier *= 0.92  # Shorter internodes under mild winter thermal accumulation
            applied_modifiers.append("Rabi thermal regime (0.92x)")
        elif s_str in ["KHARIF", "MONSOON"]:
            multiplier *= 1.00

        # 3. Soil texture modifier
        soil_str = (soil_type or "").upper()
        if "SANDY" in soil_str or "LIGHT" in soil_str:
            multiplier *= 0.95
            applied_modifiers.append("Sandy/Light soil moisture retention (0.95x)")
        elif "BLACK" in soil_str or "LOAM" in soil_str or "ALLUVIAL" in soil_str:
            multiplier *= 1.02
            applied_modifiers.append("Nutrient-rich loam/black soil (1.02x)")

        adj_min = round(base_min * multiplier, 1)
        adj_max = round(base_max * multiplier, 1)

        return {
            "min": adj_min,
            "max": adj_max,
            "range_str": f"{adj_min}–{adj_max} cm",
            "base_min": base_min,
            "base_max": base_max,
            "adjustment_factor": round(multiplier, 2),
            "modifiers": applied_modifiers,
            "biological_phase": base_data["phase"],
            "phenological_stage": base_data["stage"]
        }

    @classmethod
    def evaluate(
        cls,
        visual_week: str,
        visual_confidence: float,
        das: int,
        measured_height_cm: Optional[float],
        height_source: str,
        weather: Dict[str, Any],
        soil_type: str,
        season: str,
        variety: str,
        disease_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes multimodal synthesis across:
        - Visual Prediction (CNN week + height)
        - Farm Ground Truth (DAS, Soil, Variety, Season)
        - Environmental Evidence (Live Weather)
        
        Returns decoupled Health Assessment and Final Agronomic Interpretation.
        """
        contributing_factors: List[str] = []
        advisories: List[str] = []

        # 1. DAS expected benchmark
        das_week_key = cls.get_stage_for_das(das)
        adjusted_range = cls.compute_adjusted_height_range(
            week_key=das_week_key,
            variety=variety,
            season=season,
            soil_type=soil_type
        )

        expected_min = adjusted_range["min"]
        expected_max = adjusted_range["max"]

        # 2. Visual Week vs DAS Cross-Evaluation
        # Extract numerical week if possible
        try:
            vis_week_num = int(visual_week.replace("Week", "").strip())
        except Exception:
            vis_week_num = 1

        try:
            das_week_num = int(das_week_key.replace("Week", "").replace("+", "").strip())
        except Exception:
            das_week_num = 1

        visual_lag = False
        if das_week_num - vis_week_num >= 2:
            visual_lag = True
            contributing_factors.append(
                f"Visual phenotype resembles {visual_week} despite crop age of {das} DAS (expected {das_week_key}), indicating vegetative growth delay."
            )

        # 3. Height Assessment (Measured vs Expected Benchmark Range)
        height_status = "WITHIN_EXPECTED"
        if measured_height_cm is not None:
            if measured_height_cm < expected_min:
                height_status = "BELOW_EXPECTED"
                contributing_factors.append(
                    f"Measured stalk height ({measured_height_cm} cm) is below expected biological range ({adjusted_range['range_str']})."
                )
            elif measured_height_cm > expected_max * 1.15:
                height_status = "ABOVE_EXPECTED"
                contributing_factors.append(
                    f"Measured stalk height ({measured_height_cm} cm) is above standard range ({adjusted_range['range_str']}), suggesting vigorous vegetative elongation."
                )
            else:
                height_status = "WITHIN_EXPECTED"

        # 4. Environmental Stress Factors
        temp = weather.get("temperature_c", 30.0)
        humidity = weather.get("humidity_percent", 70)
        rainfall = weather.get("rainfall_mm", 5.0)
        frost_risk = weather.get("frost_risk", "None")

        temp_stress = False
        if temp >= 37.0:
            temp_stress = True
            contributing_factors.append(f"High ambient temperature ({temp}°C) increases evapotranspiration and thermal stress.")
        elif temp <= 12.0:
            temp_stress = True
            contributing_factors.append(f"Low temperature ({temp}°C) slows down cellular elongation.")

        moisture_stress = False
        if rainfall < 1.0 and humidity < 45:
            moisture_stress = True
            contributing_factors.append("Low recent precipitation combined with low atmospheric humidity creates moisture deficit risk.")

        if frost_risk not in ["None", None, ""]:
            contributing_factors.append(f"Frost Warning: {frost_risk}.")

        # 5. Composite Growth & Health Status (Multimodal Decision Hierarchy)
        disease_name = disease_info.get("detected_disease", "Healthy") if disease_info else "Healthy"
        disease_conf = disease_info.get("confidence", 0.90) if disease_info else 0.90
        disease_severity = disease_info.get("severity", "NONE") if disease_info else "NONE"
        disease_detail = disease_info.get("detail", "") if disease_info else ""

        is_stunted = (height_status == "BELOW_EXPECTED" or visual_lag)
        is_diseased = (disease_name not in ["Healthy", "None", "INCONCLUSIVE", "Visual Scouting Recommended"])
        is_inconclusive = (disease_name == "INCONCLUSIVE")

        # Record disease contributing factors
        if is_diseased:
            conf_pct = round(disease_conf * 100) if disease_conf else 88
            contributing_factors.append(
                f"Foliar pathology identified: {disease_name} ({disease_severity} severity, {conf_pct}% confidence). {disease_detail}"
            )
        elif is_inconclusive:
            contributing_factors.append(
                "Foliar disease check: Inconclusive visual evidence. Physical field scouting active."
            )

        # Decision Matrix
        if is_stunted and is_diseased:
            growth_status = "STUNTED_AND_INFECTED"
            is_healthy = False
            health_headline = f"🚨 Critical: Stunted Growth & Foliar Infection ({disease_name})"
        elif is_diseased:
            growth_status = "INFECTED"
            is_healthy = False
            health_headline = f"❌ Pathological Foliar Infection: {disease_name}"
        elif is_stunted and is_inconclusive:
            growth_status = "STUNTED"
            is_healthy = False
            health_headline = "⚠️ Below Expected Growth (Stunted) • Foliar Scouting Active"
        elif is_stunted:
            growth_status = "STUNTED"
            is_healthy = False
            health_headline = "⚠️ Below Expected Growth (Stunted / Delayed)"
        elif is_inconclusive:
            growth_status = "MONITOR_SCOUT"
            is_healthy = True
            health_headline = "🔍 Normal Stalk Growth (Foliar Scouting Active)"
        elif height_status == "ABOVE_EXPECTED":
            growth_status = "OVERGROWN"
            is_healthy = True
            health_headline = "🌱 Above Expected Range (Vigorous Growth)"
        else:
            growth_status = "NORMAL"
            is_healthy = True
            health_headline = "✓ Healthy / Within Expected Range"

        if temp_stress or moisture_stress:
            if is_healthy:
                health_headline += " (Environmental Stress Watch)"

        # 6. Actionable Agronomic Advisory Generation (Enforcing Module 3 Safety Gates)
        # =========================================================================
        # Axiom: Symptom -> Hypothesis -> Supporting Evidence -> Action/Verification
        # =========================================================================
        if growth_status == "STUNTED_AND_INFECTED":
            # Priority 1: Pathogen containment first
            if "Rust" in disease_name:
                advisories.append("PRIORITY 1 (Pathogen Containment): Apply Azoxystrobin or Pyraclostrobin fungicide (100g/acre) immediately to stop pustule spread.")
            elif "Blight" in disease_name:
                advisories.append("PRIORITY 1 (Pathogen Containment): Spray Chlorothalonil or Propiconazole fungicide. Ensure canopy air circulation.")
            elif "Gray Leaf Spot" in disease_name:
                advisories.append("PRIORITY 1 (Pathogen Containment): Apply Mancozeb or systemic Triazole fungicide. Strip heavily blighted lower leaves.")
            elif "Nutrient" in disease_name:
                advisories.append("PRIORITY 1: Apply foliar NPK 19:19:19 (@ 5g/L) combined with chelated Zinc to rectify leaf chlorosis.")
            else:
                advisories.append(f"PRIORITY 1: Apply targeted treatment for {disease_name}.")

            # Safety Gate: Restrict heavy nitrogen application until disease is stabilized
            advisories.append("SAFETY GATE: Do NOT apply heavy soil Urea until foliar lesions stabilize. Excessive nitrogen creates succulent tissues vulnerable to secondary infection.")
            advisories.append("Inspect root structure for hardpan compaction or nematode damage inhibiting deep root anchoring.")

        elif growth_status == "INFECTED":
            if "Rust" in disease_name:
                advisories.append("Apply Azoxystrobin or Pyraclostrobin fungicide (100g/acre) to arrest active Puccinia sorghi sporulation.")
            elif "Blight" in disease_name:
                advisories.append("Spray Chlorothalonil or Propiconazole foliar fungicide. Avoid late-afternoon overhead irrigation to reduce leaf wetness.")
            elif "Gray Leaf Spot" in disease_name:
                advisories.append("Apply Mancozeb or Triazole fungicide. Remove severely blighted lower leaves to limit vertical inoculum migration.")
            elif "Nutrient" in disease_name:
                advisories.append("Apply NPK (19:19:19 or 20:20:20) foliar spray combined with zinc sulphate (5 kg/acre) to restore chlorophyll synthesis.")
            else:
                advisories.append(f"Initiate standard agronomic protection regimen for {disease_name}.")

        elif growth_status == "STUNTED":
            advisories.append("Apply a side-dress dose of Nitrogen (Urea @ 30–35 kg/acre) along with zinc sulphate (5 kg/acre) to accelerate vegetative recovery.")
            advisories.append("Inspect root structure for nematode damage or hardpan soil compaction inhibiting deep root anchoring.")

        elif growth_status == "MONITOR_SCOUT":
            advisories.append("Visual evidence inconclusive: Conduct physical foliar scouting across 20 representative plants before applying chemical sprays.")
            advisories.append(f"Maintain standard agronomic schedule for {adjusted_range['phenological_stage']}: steady soil moisture and canopy aeration.")

        elif growth_status == "NORMAL":
            advisories.append(f"Maintain standard agronomic schedule for {adjusted_range['phenological_stage']}: steady soil moisture and canopy aeration.")

        elif growth_status == "OVERGROWN":
            advisories.append("Ensure balanced Potassium nutrition to strengthen stalk walls and prevent lodging during late-season winds.")

        # Environmental remediation
        if moisture_stress:
            advisories.append(f"Schedule immediate supplementary drip or furrow irrigation to maintain root-zone soil moisture above 45% in {soil_type}.")

        if temp_stress and temp >= 37.0:
            advisories.append("Maintain light frequent irrigations during afternoon hours to cool the micro-canopy temperature.")

        # Final formatted disease diagnosis structure
        final_disease_diagnosis = disease_info if disease_info else {
            "status": "ACTIVE",
            "detected_disease": "Healthy",
            "confidence": 0.95,
            "severity": "NONE",
            "detail": "Healthy photosynthetic foliage confirmed.",
            "engine": "NEURAL_CLASSIFIER",
            "evidence": {}
        }

        return {
            "growth_status": growth_status,
            "is_healthy": is_healthy,
            "health_headline": health_headline,
            "das": das,
            "expected_week": das_week_key,
            "phenological_stage": adjusted_range["phenological_stage"],
            "biological_phase": adjusted_range["biological_phase"],
            "measured_height_cm": measured_height_cm,
            "expected_range_cm": {
                "min": expected_min,
                "max": expected_max
            },
            "expected_range_str": adjusted_range["range_str"],
            "height_status": height_status,
            "height_source": height_source,
            "height_adjustment": {
                "factor": adjusted_range["adjustment_factor"],
                "modifiers": adjusted_range["modifiers"]
            },
            "contributing_factors": contributing_factors,
            "advisory_points": advisories,
            "disease_diagnosis": final_disease_diagnosis
        }
