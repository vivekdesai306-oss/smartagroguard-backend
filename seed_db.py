import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "agroguard")

# --- 1. Crop Growth Benchmarks (Weeks 1 to 11 for Maize / Corn) ---
CROP_GROWTH_BENCHMARKS = [
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 1", "min_height_cm": 5.0, "max_height_cm": 15.0, "das_min": 1, "das_max": 7},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 2", "min_height_cm": 15.0, "max_height_cm": 30.0, "das_min": 8, "das_max": 14},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 3", "min_height_cm": 30.0, "max_height_cm": 50.0, "das_min": 15, "das_max": 21},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 4", "min_height_cm": 45.0, "max_height_cm": 70.0, "das_min": 22, "das_max": 28},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 5", "min_height_cm": 50.0, "max_height_cm": 80.0, "das_min": 29, "das_max": 35},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 6", "min_height_cm": 80.0, "max_height_cm": 120.0, "das_min": 36, "das_max": 42},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 7", "min_height_cm": 120.0, "max_height_cm": 160.0, "das_min": 43, "das_max": 49},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 8", "min_height_cm": 150.0, "max_height_cm": 200.0, "das_min": 50, "das_max": 56},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 9", "min_height_cm": 180.0, "max_height_cm": 230.0, "das_min": 57, "das_max": 63},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 10", "min_height_cm": 200.0, "max_height_cm": 250.0, "das_min": 64, "das_max": 70},
    {"crop_type": "Corn", "variety": "GAYMH-1", "week": "Week 11", "min_height_cm": 200.0, "max_height_cm": 250.0, "das_min": 71, "das_max": 77},
]

# --- 2. Diagnostic Rules Matrix ---
DIAGNOSTIC_RULES = [
    {
        "rule_id": "RULE_WATER_STRESS",
        "conditions": {
            "height_status": "BELOW_EXPECTED",
            "rainfall_threshold_mm": 2.0,
            "rainfall_operator": "LT",
            "disease": "Healthy"
        },
        "triage": "Moisture Deficit Investigation",
        "pathway": "Irrigation & Water Stress Pathway",
        "hypothesis": "Water_Stress_Suspected",
        "action": "RESTORE_WATER_AVAILABILITY",
        "nitrogen_lockout": True
    },
    {
        "rule_id": "RULE_NUTRIENT_DEFICIENCY",
        "conditions": {
            "height_status": "BELOW_EXPECTED",
            "rainfall_threshold_mm": 2.0,
            "rainfall_operator": "GTE",
            "observation_contains": "lower_leaf_chlorosis"
        },
        "triage": "Nutrient Depletion Investigation",
        "pathway": "Fertility & Nutrition Pathway",
        "hypothesis": "Nutrient_Deficiency_Suspected",
        "action": "FERTILIZER_RECOMMENDATION",
        "nitrogen_lockout": False
    },
    {
        "rule_id": "RULE_INDETERMINATE_STUNTING",
        "conditions": {
            "height_status": "BELOW_EXPECTED",
            "rainfall_threshold_mm": 2.0,
            "rainfall_operator": "GTE",
            "disease": "Healthy",
            "no_chlorosis": True
        },
        "triage": "Indeterminate Stunting Investigation",
        "pathway": "Rootzone & Soil Physical Scouting Pathway",
        "hypothesis": "Insufficient_Evidence",
        "action": "INSUFFICIENT_EVIDENCE",
        "nitrogen_lockout": True
    },
    {
        "rule_id": "RULE_PATHOLOGY_CONFIRMED",
        "conditions": {
            "disease_not_healthy": True,
            "min_disease_confidence": 0.75
        },
        "triage": "Active Pathology Investigation",
        "pathway": "Pathology & Curative Protection Pathway",
        "hypothesis": "Disease_Stress_Suspected",
        "action": "PESTICIDE_RECOMMENDATION",
        "nitrogen_lockout": False
    },
    {
        "rule_id": "RULE_PATHOLOGY_UNCONFIRMED",
        "conditions": {
            "disease_not_healthy": True,
            "max_disease_confidence": 0.75
        },
        "triage": "Unconfirmed Symptom Investigation",
        "pathway": "Field Scouting & Daylight Re-scan Pathway",
        "hypothesis": "Disease_Stress_Suspected",
        "action": "PERFORM_FIELD_INSPECTION",
        "nitrogen_lockout": True
    },
    {
        "rule_id": "RULE_PHENOLOGICAL_MAINTENANCE",
        "conditions": {
            "height_status": "WITHIN_EXPECTED",
            "disease": "Healthy"
        },
        "triage": "Phenological Maintenance",
        "pathway": "Baseline Agronomy Pathway",
        "hypothesis": "Healthy_Optimal",
        "action": "FERTILIZER_RECOMMENDATION",
        "nitrogen_lockout": False
    }
]

# --- 3. Dynamic Fertilizer Catalog ---
FERTILIZER_RECOMMENDATIONS = [
    {
        "fertilizer_id": "f_corn_w1",
        "growth_week": "Week 1",
        "crop_type": "Corn",
        "target_condition": "Baseline Growth",
        "product_name": "Starter N-P-K (18-46-0 DAP)",
        "active_ingredient": "Nitrogen 18%, Phosphorus (P2O5) 46%",
        "formulation": "Granular Side-Dress",
        "unit_rate_per_acre_val": 25.0,
        "unit_rate_per_acre_str": "25 kg/acre",
        "unit_of_measure": "kg",
        "water_dilution": "N/A (Soil Granular)",
        "application_method": "Soil basal placement during sowing or early emergence",
        "timing": "Morning or Late Evening",
        "safety_notes": "Place granular fertilizer 5 cm to the side and 5 cm deeper than seed level to avoid seed burn."
    },
    {
        "fertilizer_id": "f_corn_w3",
        "growth_week": "Week 3",
        "crop_type": "Corn",
        "target_condition": "Vegetative Elongation",
        "product_name": "Agricultural Urea (46-0-0)",
        "active_ingredient": "Ammoniacal Nitrogen 46%",
        "formulation": "Prilled Granular",
        "unit_rate_per_acre_val": 40.0,
        "unit_rate_per_acre_str": "40 kg/acre",
        "unit_of_measure": "kg",
        "water_dilution": "N/A (Soil Side-Dress)",
        "application_method": "Inter-row soil side-dressing followed by light irrigation",
        "timing": "Early Morning",
        "safety_notes": "Ensure soil is moist before application. Avoid direct contact with wet foliage."
    },
    {
        "fertilizer_id": "f_corn_w5",
        "growth_week": "Week 5",
        "crop_type": "Corn",
        "target_condition": "Rapid Elongation & Knee-High Phase",
        "product_name": "Urea (46% N) + Zinc Sulphate (21% Zn)",
        "active_ingredient": "Nitrogen 46% + Elemental Zinc 21%",
        "formulation": "Soil Side-Dress Granular + Foliar Micronutrient Spray",
        "unit_rate_per_acre_val": 35.0,
        "unit_rate_per_acre_str": "35 kg Urea + 5 kg Zinc Sulphate per acre",
        "unit_of_measure": "kg",
        "water_dilution": "200 Litres water per acre for foliar zinc portion",
        "application_method": "Soil side-dressing for Urea; foliar spray for Zinc",
        "timing": "Cool hours of morning or late afternoon",
        "safety_notes": "Do not mix concentrated zinc sulphate directly with alkaline pesticides."
    },
    {
        "fertilizer_id": "f_corn_nutrient_deficiency",
        "growth_week": "Any",
        "crop_type": "Corn",
        "target_condition": "Nutrient_Deficiency_Suspected",
        "product_name": "Chelated N-P-K (19-19-19) + Micronutrient Complex",
        "active_ingredient": "Balanced NPK 19% + Zn, Fe, B, Mn",
        "formulation": "Water Soluble Foliar Powder",
        "unit_rate_per_acre_val": 1.0,
        "unit_rate_per_acre_str": "1.0 kg/acre",
        "unit_of_measure": "kg",
        "water_dilution": "200 Litres of clean water per acre",
        "application_method": "Foliar canopy spray using knapsack nozzle",
        "timing": "Early Morning (6:00 AM – 9:00 AM)",
        "safety_notes": "Ensure full canopy coverage. Do not spray during peak midday sunlight (> 32°C)."
    }
]

# --- 4. Dynamic Pesticide & Pathology Catalog ---
PESTICIDE_RECOMMENDATIONS = [
    {
        "pesticide_id": "p_corn_rust",
        "crop_type": "Corn",
        "target_disease": "Corn Common Rust",
        "product_name": "Amistar Top (Azoxystrobin 18.2% + Difenoconazole 11.4% SC)",
        "active_ingredient": "Azoxystrobin 18.2% + Difenoconazole 11.4%",
        "formulation": "Suspension Concentrate (SC)",
        "unit_rate_per_acre_val": 200.0,
        "unit_rate_per_acre_str": "200 ml/acre",
        "unit_of_measure": "ml",
        "water_dilution": "200 Litres water per acre",
        "application_method": "Foliar spray with hollow-cone nozzle covering top and lower leaves",
        "timing": "Morning hours after dew dries",
        "rainfastness_hours": 3.0,
        "pre_harvest_interval_days": 14,
        "safety_notes": "Wear protective gloves and mask. Avoid spraying near water bodies."
    },
    {
        "pesticide_id": "p_corn_leaf_spot",
        "crop_type": "Corn",
        "target_disease": "Corn Gray Leaf Spot",
        "product_name": "Tilt 25 EC (Propiconazole 25% EC)",
        "active_ingredient": "Propiconazole 25% EC",
        "formulation": "Emulsifiable Concentrate (EC)",
        "unit_rate_per_acre_val": 200.0,
        "unit_rate_per_acre_str": "200 ml/acre",
        "unit_of_measure": "ml",
        "water_dilution": "200 Litres water per acre",
        "application_method": "Foliar canopy spray at first sign of rectangular lesions",
        "timing": "Late Afternoon (4:00 PM – 6:30 PM)",
        "rainfastness_hours": 2.0,
        "pre_harvest_interval_days": 21,
        "safety_notes": "Highly toxic to aquatic flora. Maintain 10m buffer zone from ponds."
    },
    {
        "pesticide_id": "p_corn_blight",
        "crop_type": "Corn",
        "target_disease": "Northern Leaf Blight",
        "product_name": "Kavach (Chlorothalonil 75% WP)",
        "active_ingredient": "Chlorothalonil 75%",
        "formulation": "Wettable Powder (WP)",
        "unit_rate_per_acre_val": 400.0,
        "unit_rate_per_acre_str": "400 g/acre",
        "unit_of_measure": "g",
        "water_dilution": "200 Litres water per acre",
        "application_method": "Preventative/Curative foliar spray",
        "timing": "Morning hours",
        "rainfastness_hours": 4.0,
        "pre_harvest_interval_days": 14,
        "safety_notes": "Stir solution thoroughly to prevent powder settling in tank."
    },
    {
        "pesticide_id": "p_corn_faw",
        "crop_type": "Corn",
        "target_disease": "Fall Armyworm (Spodoptera frugiperda)",
        "product_name": "Proclaim (Emamectin Benzoate 5% SG)",
        "active_ingredient": "Emamectin Benzoate 5% SG",
        "formulation": "Soluble Granules (SG)",
        "unit_rate_per_acre_val": 80.0,
        "unit_rate_per_acre_str": "80 g/acre",
        "unit_of_measure": "g",
        "water_dilution": "200 Litres water per acre",
        "application_method": "Directed spray straight down into central plant whorls",
        "timing": "Early Morning or Late Afternoon",
        "rainfastness_hours": 3.0,
        "pre_harvest_interval_days": 14,
        "safety_notes": "Ensure hollow-cone nozzle is centered directly over the whorl where larvae feed."
    },
    {
        "pesticide_id": "p_corn_stem_borer",
        "crop_type": "Corn",
        "target_disease": "Spotted Stem Borer (Chilo partellus)",
        "product_name": "Coragen (Chlorantraniliprole 18.5% SC)",
        "active_ingredient": "Chlorantraniliprole 18.5% SC",
        "formulation": "Suspension Concentrate (SC)",
        "unit_rate_per_acre_val": 80.0,
        "unit_rate_per_acre_str": "80 ml/acre",
        "unit_of_measure": "ml",
        "water_dilution": "200 Litres water per acre",
        "application_method": "Foliar and lower stem collar spray",
        "timing": "Morning hours",
        "rainfastness_hours": 2.0,
        "pre_harvest_interval_days": 14,
        "safety_notes": "Spray before larvae tunnel deep into the stalk internodes."
    },
    {
        "pesticide_id": "p_corn_aphid",
        "crop_type": "Corn",
        "target_disease": "Corn Leaf Aphids (Rhopalosiphum maidis)",
        "product_name": "Confidor (Imidacloprid 17.8% SL)",
        "active_ingredient": "Imidacloprid 17.8% SL",
        "formulation": "Soluble Liquid (SL)",
        "unit_rate_per_acre_val": 60.0,
        "unit_rate_per_acre_str": "60 ml/acre",
        "unit_of_measure": "ml",
        "water_dilution": "200 Litres water per acre",
        "application_method": "Foliar spray on upper leaf surface and tassel zone",
        "timing": "Morning or Late Evening",
        "rainfastness_hours": 2.0,
        "pre_harvest_interval_days": 21,
        "safety_notes": "Avoid spraying during active honeybee foraging in midday."
    }
]

# --- 5. Safety Validation & Restriction Rules ---
TREATMENT_RESTRICTIONS = [
    {
        "restriction_id": "RST_WIND_DRIFT",
        "parameter": "wind_speed_kmh",
        "max_limit": 15.0,
        "headline": "High Wind Drift Risk",
        "action": "HOLD_SPRAY",
        "reason": "Wind speed exceeds 15 km/h limit. Chemical spray drift poses environmental & off-target damage risk."
    },
    {
        "restriction_id": "RST_RAINFASTNESS",
        "parameter": "hours_until_rain",
        "headline": "Rain Washout Warning",
        "action": "HOLD_SPRAY",
        "reason": "Forecast rainfall is closer than product rainfastness window. Spray will be washed off."
    },
    {
        "restriction_id": "RST_NITROGEN_RUST_CONFLICT",
        "conflict_pair": ["Nitrogen", "Corn Common Rust"],
        "headline": "Chemical Contra-Indication",
        "action": "LOCK_OUT_NITROGEN",
        "reason": "High nitrogen application during active fungal rust infection fuels spore proliferation."
    },
    {
        "restriction_id": "RST_WATER_STRESS_NITROGEN_BURNING",
        "conflict_pair": ["Nitrogen", "Water_Stress_Suspected"],
        "headline": "Osmotic Root Burn Warning",
        "action": "LOCK_OUT_NITROGEN",
        "reason": "Applying nitrogen fertilizer to water-stressed soil causes root cell desiccation and severe leaf scorch."
    }
]

# --- 6. Agro-Climatic Normals (Module 4 Weather Intelligence) ---
AGRO_CLIMATIC_NORMALS = [
    # Middle Gujarat Zone III (Panchmahal, Anand, Vadodara, Kheda)
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 1, "normal_min_temperature_c": 12.5, "normal_max_temperature_c": 28.0, "normal_rainfall_mm": 1.0, "normal_relative_humidity_percent": 48.0, "normal_wind_speed_kmh": 7.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 2, "normal_min_temperature_c": 14.8, "normal_max_temperature_c": 30.5, "normal_rainfall_mm": 1.5, "normal_relative_humidity_percent": 42.0, "normal_wind_speed_kmh": 8.2, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 3, "normal_min_temperature_c": 19.2, "normal_max_temperature_c": 35.6, "normal_rainfall_mm": 2.0, "normal_relative_humidity_percent": 36.0, "normal_wind_speed_kmh": 9.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 4, "normal_min_temperature_c": 23.8, "normal_max_temperature_c": 39.2, "normal_rainfall_mm": 3.0, "normal_relative_humidity_percent": 35.0, "normal_wind_speed_kmh": 11.2, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 5, "normal_min_temperature_c": 27.0, "normal_max_temperature_c": 41.5, "normal_rainfall_mm": 8.0, "normal_relative_humidity_percent": 48.0, "normal_wind_speed_kmh": 14.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 6, "normal_min_temperature_c": 26.5, "normal_max_temperature_c": 37.0, "normal_rainfall_mm": 120.0, "normal_relative_humidity_percent": 68.0, "normal_wind_speed_kmh": 15.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 7, "normal_min_temperature_c": 25.0, "normal_max_temperature_c": 32.5, "normal_rainfall_mm": 280.0, "normal_relative_humidity_percent": 82.0, "normal_wind_speed_kmh": 13.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 8, "normal_min_temperature_c": 24.5, "normal_max_temperature_c": 31.0, "normal_rainfall_mm": 240.0, "normal_relative_humidity_percent": 84.0, "normal_wind_speed_kmh": 12.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 9, "normal_min_temperature_c": 23.5, "normal_max_temperature_c": 31.8, "normal_rainfall_mm": 165.0, "normal_relative_humidity_percent": 76.0, "normal_wind_speed_kmh": 9.2, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 10, "normal_min_temperature_c": 20.5, "normal_max_temperature_c": 34.0, "normal_rainfall_mm": 25.0, "normal_relative_humidity_percent": 58.0, "normal_wind_speed_kmh": 7.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 11, "normal_min_temperature_c": 16.0, "normal_max_temperature_c": 31.5, "normal_rainfall_mm": 8.0, "normal_relative_humidity_percent": 52.0, "normal_wind_speed_kmh": 6.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "ZONE_III", "district": "Panchmahal", "month": 12, "normal_min_temperature_c": 13.0, "normal_max_temperature_c": 29.0, "normal_rainfall_mm": 2.0, "normal_relative_humidity_percent": 50.0, "normal_wind_speed_kmh": 7.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    # DEFAULT zone for any unmapped regions
    {"zone": "DEFAULT", "district": "All", "month": 1, "normal_min_temperature_c": 13.0, "normal_max_temperature_c": 27.5, "normal_rainfall_mm": 2.0, "normal_relative_humidity_percent": 50.0, "normal_wind_speed_kmh": 8.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 2, "normal_min_temperature_c": 15.0, "normal_max_temperature_c": 30.0, "normal_rainfall_mm": 2.0, "normal_relative_humidity_percent": 45.0, "normal_wind_speed_kmh": 8.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 3, "normal_min_temperature_c": 19.5, "normal_max_temperature_c": 34.5, "normal_rainfall_mm": 3.0, "normal_relative_humidity_percent": 40.0, "normal_wind_speed_kmh": 9.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 4, "normal_min_temperature_c": 24.0, "normal_max_temperature_c": 38.0, "normal_rainfall_mm": 5.0, "normal_relative_humidity_percent": 38.0, "normal_wind_speed_kmh": 11.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 5, "normal_min_temperature_c": 26.5, "normal_max_temperature_c": 40.0, "normal_rainfall_mm": 10.0, "normal_relative_humidity_percent": 50.0, "normal_wind_speed_kmh": 14.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 6, "normal_min_temperature_c": 26.0, "normal_max_temperature_c": 36.0, "normal_rainfall_mm": 110.0, "normal_relative_humidity_percent": 70.0, "normal_wind_speed_kmh": 14.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 7, "normal_min_temperature_c": 24.8, "normal_max_temperature_c": 32.0, "normal_rainfall_mm": 260.0, "normal_relative_humidity_percent": 80.0, "normal_wind_speed_kmh": 13.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 8, "normal_min_temperature_c": 24.0, "normal_max_temperature_c": 31.0, "normal_rainfall_mm": 230.0, "normal_relative_humidity_percent": 82.0, "normal_wind_speed_kmh": 11.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 9, "normal_min_temperature_c": 23.0, "normal_max_temperature_c": 32.0, "normal_rainfall_mm": 150.0, "normal_relative_humidity_percent": 75.0, "normal_wind_speed_kmh": 9.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 10, "normal_min_temperature_c": 20.0, "normal_max_temperature_c": 33.5, "normal_rainfall_mm": 30.0, "normal_relative_humidity_percent": 60.0, "normal_wind_speed_kmh": 7.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 11, "normal_min_temperature_c": 16.5, "normal_max_temperature_c": 31.0, "normal_rainfall_mm": 10.0, "normal_relative_humidity_percent": 55.0, "normal_wind_speed_kmh": 7.0, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
    {"zone": "DEFAULT", "district": "All", "month": 12, "normal_min_temperature_c": 13.5, "normal_max_temperature_c": 28.5, "normal_rainfall_mm": 3.0, "normal_relative_humidity_percent": 52.0, "normal_wind_speed_kmh": 7.5, "source": "IMD", "source_version": "2024", "effective_from": "2024-01-01"},
]

async def seed():
    print(f"Connecting to MongoDB at {MONGODB_URL}...")
    try:
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=3000)
        db = client[DATABASE_NAME]
        
        collections_to_seed = {
            "crop_growth_benchmarks": CROP_GROWTH_BENCHMARKS,
            "diagnostic_rules": DIAGNOSTIC_RULES,
            "fertilizer_recommendations": FERTILIZER_RECOMMENDATIONS,
            "pesticide_recommendations": PESTICIDE_RECOMMENDATIONS,
            "treatment_restrictions": TREATMENT_RESTRICTIONS,
            "agro_climatic_normals": AGRO_CLIMATIC_NORMALS
        }
        
        for coll_name, data in collections_to_seed.items():
            print(f"Clearing and seeding collection '{coll_name}' ({len(data)} items)...")
            await db[coll_name].delete_many({})
            res = await db[coll_name].insert_many(data)
            print(f"  -> Seeded {len(res.inserted_ids)} records into '{coll_name}'")

        # --- Create Indexes for Module 4 Collections ---
        print("Ensuring indexes for Module 4 (Weather & Alerts)...")
        # weather_alerts indexes
        await db["weather_alerts"].create_index("alert_id", unique=True)
        await db["weather_alerts"].create_index("farm_id")
        await db["weather_alerts"].create_index([("farm_id", 1), ("is_active", 1)])
        await db["weather_alerts"].create_index([("farm_id", 1), ("alert_type", 1), ("alert_date", -1)])

        # agro_climatic_normals indexes
        await db["agro_climatic_normals"].create_index([("zone", 1), ("month", 1)], unique=True)
        await db["agro_climatic_normals"].create_index([("district", 1), ("month", 1)])

        # notification_delivery_logs indexes
        await db["notification_delivery_logs"].create_index("notification_id", unique=True)
        await db["notification_delivery_logs"].create_index([("notification_key", 1), ("channel", 1)], unique=True)
        await db["notification_delivery_logs"].create_index("farm_id")

        print("Module 4 indexes created successfully!")

        client.close()
        print("All database collections seeded and indexed successfully!")
    except Exception as e:
        print(f"MongoDB connection warning during seed: {e}")

if __name__ == "__main__":
    asyncio.run(seed())

