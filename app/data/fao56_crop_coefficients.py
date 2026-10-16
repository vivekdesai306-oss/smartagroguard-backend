"""
FAO-56 Penman-Monteith Crop Coefficients & Soil Water Holding Capacities
Target Crop: Maize / Hybrid Corn (Zea mays L.)
Reference: FAO Irrigation and Drainage Paper No. 56 (Crop Evapotranspiration)
"""

# FAO-56 Crop Coefficients (Kc) for Maize across Biological Growth Stages
MAIZE_FAO56_KC_STAGES = {
    "INITIAL": {
        "stage_code": "KC_INI",
        "stage_name": "Initial Stage / Emergence (VE - V2)",
        "das_range": (0, 15),
        "kc_value": 0.40,
        "root_depth_m": 0.25,
        "mad_fraction": 0.55,  # Management Allowed Depletion fraction
        "description": "Ground cover < 10%, evaporation from bare wet soil dominates."
    },
    "DEVELOPMENT": {
        "stage_code": "KC_DEV",
        "stage_name": "Crop Development (V3 - V8 Rapid Growth)",
        "das_range": (16, 42),
        "kc_value": 0.80,
        "root_depth_m": 0.60,
        "mad_fraction": 0.50,
        "description": "Ground cover expands from 10% to 75%, rapid vegetative internode surge."
    },
    "MID_SEASON": {
        "stage_code": "KC_MID",
        "stage_name": "Mid-Season / Tasseling & Silking (VT - R2 Grain Fill)",
        "das_range": (43, 75),
        "kc_value": 1.15,
        "root_depth_m": 1.00,
        "mad_fraction": 0.40,  # Highly sensitive to moisture stress (MAD 40%)
        "description": "Peak water consumption window. Severe moisture stress reduces yield by 3-4% per day."
    },
    "LATE_SEASON": {
        "stage_code": "KC_LATE",
        "stage_name": "Late Season / Dough & Starch Hardening (R3 - R5)",
        "das_range": (76, 100),
        "kc_value": 0.75,
        "root_depth_m": 1.00,
        "mad_fraction": 0.55,
        "description": "Senescence of lower leaves, starch line progresses towards kernel base."
    },
    "MATURATION": {
        "stage_code": "KC_END",
        "stage_name": "Maturity / Black Layer (R6 Physiological Harvest)",
        "das_range": (101, 120),
        "kc_value": 0.50,
        "root_depth_m": 1.00,
        "mad_fraction": 0.65,
        "description": "Grain dry-down period. Zero further irrigation required."
    }
}

# Indian Soil Hydraulic Constants & Infiltration Characteristics
INDIAN_SOIL_HYDRAULICS = {
    "Sandy Loam (Goradu)": {
        "soil_type": "Sandy Loam (Goradu)",
        "field_capacity_pct": 18.0,       # Volumetric water content at Field Capacity (%)
        "wilting_point_pct": 8.0,         # Volumetric water content at Permanent Wilting Point (%)
        "total_available_water_mm_per_m": 100.0, # TAW in mm water per meter soil depth
        "infiltration_rate_mm_per_hr": 25.0,     # Basic steady infiltration rate
        "drainage_class": "Well-Drained",
        "drip_emitter_spacing_m": 0.40,
        "typical_regions": ["Gujarat Plains (Panchmahal, Dahod)", "Rajasthan Plains", "Punjab Semi-Arid"]
    },
    "Clay Loam": {
        "soil_type": "Clay Loam",
        "field_capacity_pct": 32.0,
        "wilting_point_pct": 17.0,
        "total_available_water_mm_per_m": 150.0,
        "infiltration_rate_mm_per_hr": 10.0,
        "drainage_class": "Moderate",
        "drip_emitter_spacing_m": 0.50,
        "typical_regions": ["Bihar Gangetic Alluvium (Begusarai)", "Eastern UP", "West Bengal"]
    },
    "Black Cotton Soil (Vertisol)": {
        "soil_type": "Black Cotton Soil (Vertisol)",
        "field_capacity_pct": 38.0,
        "wilting_point_pct": 20.0,
        "total_available_water_mm_per_m": 180.0,
        "infiltration_rate_mm_per_hr": 5.0,
        "drainage_class": "Slow / Prone to Waterlogging",
        "drip_emitter_spacing_m": 0.60,
        "typical_regions": ["Maharashtra Deccan (Aurangabad)", "Madhya Pradesh (Chhindwara)", "Karnataka (Davangere)"]
    },
    "Alluvial Silt Loam": {
        "soil_type": "Alluvial Silt Loam",
        "field_capacity_pct": 26.0,
        "wilting_point_pct": 11.0,
        "total_available_water_mm_per_m": 150.0,
        "infiltration_rate_mm_per_hr": 15.0,
        "drainage_class": "Optimal",
        "drip_emitter_spacing_m": 0.45,
        "typical_regions": ["Gangetic Plains", "Telangana Plateau"]
    }
}
