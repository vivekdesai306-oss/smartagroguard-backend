"""
Agricultural Knowledge Base and Suitability Dataset for Maize (Zea mays / Corn / Makai) in India.
Contains multi-tier recommendations:
1. Village / Taluka level overrides
2. District level data
3. Agro-Climatic Zone definitions
4. State level baselines
5. National fallbacks
"""

# 15 Major Planning Commission Agro-Climatic Zones of India
AGRO_CLIMATIC_ZONES = {
    "ZONE_1": {
        "name": "Western Himalayan Region",
        "states": ["Jammu and Kashmir", "Himachal Pradesh", "Uttarakhand"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "Temperate to sub-tropical valleys, high rainfall in monsoon, cool summer temperatures.",
        "soil_suitability": "Brown hill soil, Podzolic, well-drained gravelly sandy loam.",
        "optimal_ph": "5.5 - 7.0",
        "default_varieties": ["Pusa Composite 3", "Early Composite", "Parvati", "Vivek Sankul 11"]
    },
    "ZONE_2": {
        "name": "Eastern Himalayan Region",
        "states": ["Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Sikkim", "Tripura"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "High humidity and heavy rainfall. Cultivated on terraced hill slopes and sub-mountainous tracts.",
        "soil_suitability": "Red and yellow acidic soils, Alluvial terraces.",
        "optimal_ph": "5.0 - 6.5",
        "default_varieties": ["Megha Maize 1", "RCM 76", "DA 61 A", "HQPM 1"]
    },
    "ZONE_3": {
        "name": "Lower Gangetic Plains Region",
        "states": ["West Bengal"],
        "maize_suitable": True,
        "primary_season": "RABI",
        "description": "High alluvial moisture, flood-prone Kharif, exceptional high-yielding Rabi maize tract.",
        "soil_suitability": "Deltaic Alluvium, Sandy Clay Loam.",
        "optimal_ph": "6.0 - 7.5",
        "default_varieties": ["Pioneer 30V92", "NK 6240", "Bio 9681", "PAC 751"]
    },
    "ZONE_4": {
        "name": "Middle Gangetic Plains Region",
        "states": ["Bihar", "Uttar Pradesh (Eastern)"],
        "maize_suitable": True,
        "primary_season": "RABI", # Prominent for both Kharif and high-productivity Rabi
        "description": "Fertile Gangetic alluvium. Bihar is one of India's highest-yielding winter maize hubs.",
        "soil_suitability": "Rich Deep Alluvium, Loamy Silt, Well-drained Sandy Loam.",
        "optimal_ph": "6.0 - 7.5",
        "default_varieties": ["Shaktiman 1", "Shaktiman 2", "Shaktiman 3", "HQPM 1", "DKC 9081", "P3501"]
    },
    "ZONE_5": {
        "name": "Upper Gangetic Plains Region",
        "states": ["Uttar Pradesh (Western & Central)"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "Intensively irrigated, sub-tropical continental climate.",
        "soil_suitability": "Alluvial, Sandy loam to Clay loam.",
        "optimal_ph": "6.2 - 7.8",
        "default_varieties": ["Pusa HM 4", "Pusa HM 8", "Pusa HM 9", "Ganga 11", "Kanchan"]
    },
    "ZONE_6": {
        "name": "Trans-Gangetic Plains Region",
        "states": ["Punjab", "Haryana", "Delhi", "Rajasthan (Ganganagar)"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "Semi-arid to sub-tropical, high adoption of spring and Kharif hybrids.",
        "soil_suitability": "Alluvial, calcareous loamy sand to loam.",
        "optimal_ph": "6.5 - 8.0",
        "default_varieties": ["PMH 1", "PMH 3", "HQPM 5", "Bio 9637", "Pioneer 1844"]
    },
    "ZONE_7": {
        "name": "Eastern Plateau and Hills Region",
        "states": ["Jharkhand", "Odisha", "Chhattisgarh", "West Bengal (Purulia)"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "Undulating terrain, red and lateritic soils, rainfed tribal belts.",
        "soil_suitability": "Red and Laterite soil, Sandy loam to gravelly.",
        "optimal_ph": "5.5 - 6.8",
        "default_varieties": ["Birsa Vikas Makka 2", "HQPM 1", "PAC 740", "Bio 9544"]
    },
    "ZONE_8": {
        "name": "Central Plateau and Hills Region",
        "states": ["Madhya Pradesh", "Rajasthan (Southeastern)", "Uttar Pradesh (Bundelkhand)"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "Semi-arid to dry sub-humid, plateau terrain.",
        "soil_suitability": "Mixed Red and Black soils, Medium Black soil.",
        "optimal_ph": "6.0 - 7.8",
        "default_varieties": ["JM 12", "JM 216", "Mahi Kanchan", "Mahi Dhawal", "Bio 9681"]
    },
    "ZONE_9": {
        "name": "Western Plateau and Hills Region",
        "states": ["Maharashtra", "Madhya Pradesh (Southwest)"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "Basaltic Deccan trap, prominent Kharif and Rabi grain/fodder belt.",
        "soil_suitability": "Deep Black Cotton Soil, Clayey Loam with good surface drainage.",
        "optimal_ph": "6.5 - 8.0",
        "default_varieties": ["Rajarshi", "Karveer", "Pioneer 30R77", "DKC 9108", "Bio 9681"]
    },
    "ZONE_10": {
        "name": "Southern Plateau and Hills Region",
        "states": ["Andhra Pradesh", "Telangana", "Karnataka", "Tamil Nadu (Interior)"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "Semi-arid tropical, major maize-poultry hub in India (Davangere, Karimnagar, Warangal).",
        "soil_suitability": "Red Loam, Black Clayey Loam, Sandy Loam.",
        "optimal_ph": "6.0 - 7.5",
        "default_varieties": ["DHM 117", "DHM 121", "NK 6240", "Pioneer 30V92", "CP 818", "PAC 751"]
    },
    "ZONE_11": {
        "name": "East Coast Plains and Hills Region",
        "states": ["Andhra Pradesh (Coastal)", "Odisha (Coastal)", "Tamil Nadu (Coastal)"],
        "maize_suitable": True,
        "primary_season": "RABI",
        "description": "Coastal alluvium, optimal Rabi and zero-tillage maize after Kharif paddy.",
        "soil_suitability": "Coastal Alluvium, Deltaic Soils.",
        "optimal_ph": "6.2 - 7.6",
        "default_varieties": ["DHM 117", "Bio 9681", "P3396", "PAC 740"]
    },
    "ZONE_12": {
        "name": "West Coast Plains and Ghats Region",
        "states": ["Kerala", "Goa", "Karnataka (Coastal)", "Maharashtra (Konkan)"],
        "maize_suitable": False, # Very high continuous torrential rainfall (>2500mm), poorly drained laterite -> maize prone to waterlogging and ear rot
        "primary_season": "NONE",
        "description": "Humid tropical coastal belt with heavy monsoon precipitation.",
        "soil_suitability": "Laterite and Coastal Alluvium (Heavy leeching, high water table).",
        "optimal_ph": "4.5 - 6.0",
        "default_varieties": []
    },
    "ZONE_13": {
        "name": "Gujarat Plains and Hills Region",
        "states": ["Gujarat"],
        "maize_suitable": True,
        "primary_season": "KHARIF",
        "description": "Semi-arid to arid plains, Godhra / Panchmahal is a major maize research and production belt.",
        "soil_suitability": "Medium Black, Loamy Alluvium, Goradu (Sandy Loam).",
        "optimal_ph": "6.5 - 8.0",
        "default_varieties": ["Gujarat Anand Yellow Maize Hybrid 1 (GAYMH-1)", "GAWMH 2", "Bio 9681", "HQPM 1"]
    },
    "ZONE_14": {
        "name": "Western Dry Region",
        "states": ["Rajasthan (Western Thar Desert - Jaisalmer, Bikaner, Barmer)"],
        "maize_suitable": False, # Hyper-arid, extreme heat (>45°C), low rainfall (<150mm), sandy dune soil -> not recommended for maize
        "primary_season": "NONE",
        "description": "Hyper-arid desert ecosystem with shifting sand dunes and acute moisture deficit.",
        "soil_suitability": "Desert Sandy Soil (Low organic matter, negligible water retention).",
        "optimal_ph": "7.5 - 8.8",
        "default_varieties": []
    },
    "ZONE_15": {
        "name": "Island Region",
        "states": ["Andaman and Nicobar", "Lakshadweep"],
        "maize_suitable": False, # Island tropical ecosystem, low acreage
        "primary_season": "NONE",
        "description": "Maritime tropical islands.",
        "soil_suitability": "Coralline and coastal alluvium.",
        "optimal_ph": "6.0 - 7.5",
        "default_varieties": []
    }
}

# Regional / District Database with Specific Sowing Windows and Suitability
DISTRICT_MAIZE_DATABASE = {
    # --- GUJARAT ---
    "gujarat_panchmahal": {
        "state": "Gujarat",
        "district": "Panchmahal",
        "zone_key": "ZONE_13",
        "is_suitable": True,
        "soil_type": "Goradu (Sandy Loam) & Medium Black",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-15",
                "recommended_end": "07-15",
                "peak_period": "June 25 - July 05",
                "varieties": ["GAYMH-1", "GAWMH-2", "HQPM-1", "Bio-9681"],
                "notes": "Optimal with monsoon onset. Ideal drainage required."
            },
            "RABI": {
                "recommended_start": "10-15",
                "recommended_end": "11-25",
                "peak_period": "October 25 - November 10",
                "varieties": ["GAYMH-1", "Bio-9681", "Pioneer 30R77"],
                "notes": "Requires 4-5 assured irrigations."
            },
            "SUMMER": {
                "recommended_start": "02-15",
                "recommended_end": "03-15",
                "peak_period": "February 20 - March 05",
                "varieties": ["GAYMH-1", "PAC-751"],
                "notes": "Summer fodder or sweet corn with micro-irrigation."
            }
        }
    },
    "gujarat_dahod": {
        "state": "Gujarat",
        "district": "Dahod",
        "zone_key": "ZONE_13",
        "is_suitable": True,
        "soil_type": "Sandy Loam & Red Gravelly Loam",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-15",
                "recommended_end": "07-20",
                "peak_period": "June 20 - July 05",
                "varieties": ["GAYMH-1", "GAWMH-2", "Mahi Kanchan"],
                "notes": "Major tribal maize belt. High response to starter Nitrogen."
            },
            "RABI": {
                "recommended_start": "10-20",
                "recommended_end": "11-30",
                "peak_period": "November 01 - November 15",
                "varieties": ["Bio-9681", "Pioneer 30V92"],
                "notes": "Winter maize under borewell irrigation."
            }
        }
    },
    "gujarat_kutch": {
        "state": "Gujarat",
        "district": "Kutch",
        "zone_key": "ZONE_14",
        "is_suitable": False,
        "unsuitable_reason": "Arid saline conditions, high soil salinity, extreme summer temperatures and insufficient rainfall.",
        "soil_type": "Saline Sandy Loam",
        "seasons": {}
    },
    "gujarat_anand": {
        "state": "Gujarat",
        "district": "Anand",
        "zone_key": "ZONE_13",
        "is_suitable": True,
        "soil_type": "Goradu Soil (Deep Loam)",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-20",
                "recommended_end": "07-25",
                "peak_period": "July 01 - July 10",
                "varieties": ["GAYMH-1", "HQPM-1", "Sugar 75 (Sweet Corn)"],
                "notes": "Commercial sweet corn and grain maize."
            },
            "RABI": {
                "recommended_start": "10-15",
                "recommended_end": "11-25",
                "peak_period": "November 01 - November 10",
                "varieties": ["Bio-9681", "DKC-9108"],
                "notes": "Excellent yield under drip irrigation."
            }
        }
    },

    # --- BIHAR ---
    "bihar_begusarai": {
        "state": "Bihar",
        "district": "Begusarai",
        "zone_key": "ZONE_4",
        "is_suitable": True,
        "soil_type": "Fertile Gangetic Alluvium (Sandy Silt Loam)",
        "seasons": {
            "RABI": {
                "recommended_start": "10-15",
                "recommended_end": "11-30",
                "peak_period": "October 25 - November 15",
                "varieties": ["Shaktiman-1", "Shaktiman-2", "DKC-9081", "Pioneer 30V92", "Bio-9681"],
                "notes": "India's Maize Capital. Rabi yields exceed 8-10 tons/hectare."
            },
            "KHARIF": {
                "recommended_start": "06-10",
                "recommended_end": "07-15",
                "peak_period": "June 15 - June 30",
                "varieties": ["HQPM-1", "Shaktiman-5", "PAC-751"],
                "notes": "Protect from monsoon flood waterlogging."
            },
            "SUMMER": {
                "recommended_start": "02-01",
                "recommended_end": "03-10",
                "peak_period": "February 15 - February 28",
                "varieties": ["DKC-9081", "Bio-9544"],
                "notes": "Spring/Summer crop before Boro paddy."
            }
        }
    },
    "bihar_samastipur": {
        "state": "Bihar",
        "district": "Samastipur",
        "zone_key": "ZONE_4",
        "is_suitable": True,
        "soil_type": "Deep Calcareous Alluvial Loam",
        "seasons": {
            "RABI": {
                "recommended_start": "10-20",
                "recommended_end": "12-05",
                "peak_period": "November 01 - November 20",
                "varieties": ["Shaktiman-1", "Shaktiman-3", "P3501", "DKC-9108"],
                "notes": "Top winter maize zone."
            },
            "KHARIF": {
                "recommended_start": "06-15",
                "recommended_end": "07-20",
                "peak_period": "June 25 - July 05",
                "varieties": ["HQPM-1", "Shaktiman-4"],
                "notes": "Ensure field ridging for water drainage."
            }
        }
    },

    # --- KARNATAKA ---
    "karnataka_davangere": {
        "state": "Karnataka",
        "district": "Davangere",
        "zone_key": "ZONE_10",
        "is_suitable": True,
        "soil_type": "Red Sandy Loam to Medium Black Clay",
        "seasons": {
            "KHARIF": {
                "recommended_start": "05-25",
                "recommended_end": "07-15",
                "peak_period": "June 05 - June 20",
                "varieties": ["DHM-117", "CP-818", "NK-6240", "Pioneer 30V92"],
                "notes": "South India's highest volume maize trading center."
            },
            "RABI": {
                "recommended_start": "09-15",
                "recommended_end": "11-15",
                "peak_period": "October 01 - October 20",
                "varieties": ["PAC-751", "Bio-9681", "DHM-121"],
                "notes": "Post-monsoon Rabi crop."
            },
            "SUMMER": {
                "recommended_start": "01-15",
                "recommended_end": "02-28",
                "peak_period": "February 01 - February 15",
                "varieties": ["NK-6240", "CP-818"],
                "notes": "Bhadra canal command area summer crop."
            }
        }
    },
    "karnataka_haveri": {
        "state": "Karnataka",
        "district": "Haveri",
        "zone_key": "ZONE_10",
        "is_suitable": True,
        "soil_type": "Medium Black & Red Loamy Soil",
        "seasons": {
            "KHARIF": {
                "recommended_start": "05-25",
                "recommended_end": "07-10",
                "peak_period": "June 01 - June 15",
                "varieties": ["DHM-117", "NK-6240", "Pioneer 30R77"],
                "notes": "Dominant Kharif food and feed crop."
            }
        }
    },
    "karnataka_udupi": {
        "state": "Karnataka",
        "district": "Udupi",
        "zone_key": "ZONE_12",
        "is_suitable": False,
        "unsuitable_reason": "Coastal humid high rainfall (>3500mm), acute waterlogging, acid laterite soils unsuitable for grain maize.",
        "soil_type": "Coastal Acidic Laterite",
        "seasons": {}
    },

    # --- TELANGANA ---
    "telangana_karimnagar": {
        "state": "Telangana",
        "district": "Karimnagar",
        "zone_key": "ZONE_10",
        "is_suitable": True,
        "soil_type": "Red Sandy Loam (Chalka) & Deep Black",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-01",
                "recommended_end": "07-15",
                "peak_period": "June 10 - June 25",
                "varieties": ["DHM-117", "Bio-9681", "Pioneer 30V92", "CP-818"],
                "notes": "Highly productive Kharif maize belt."
            },
            "RABI": {
                "recommended_start": "10-01",
                "recommended_end": "11-20",
                "peak_period": "October 15 - November 05",
                "varieties": ["DKC-9108", "Bio-9681", "PAC-751"],
                "notes": "Rabi crop under well irrigation."
            }
        }
    },
    "telangana_warangal": {
        "state": "Telangana",
        "district": "Warangal",
        "zone_key": "ZONE_10",
        "is_suitable": True,
        "soil_type": "Red Loam (Chalka) & Medium Black",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-05",
                "recommended_end": "07-15",
                "peak_period": "June 15 - June 30",
                "varieties": ["DHM-117", "NK-6240", "CP-818"],
                "notes": "Feed and industrial starch cultivation."
            },
            "RABI": {
                "recommended_start": "10-05",
                "recommended_end": "11-20",
                "peak_period": "October 20 - November 05",
                "varieties": ["Bio-9681", "Pioneer 30V92"],
                "notes": "Rabi maize."
            }
        }
    },

    # --- MADHYA PRADESH ---
    "madhya pradesh_chhindwara": {
        "state": "Madhya Pradesh",
        "district": "Chhindwara",
        "zone_key": "ZONE_8",
        "is_suitable": True,
        "soil_type": "Medium Black & Sandy Clay Loam",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-15",
                "recommended_end": "07-15",
                "peak_period": "June 20 - July 02",
                "varieties": ["JM-216", "HQPM-1", "Bio-9681", "PAC-740"],
                "notes": "Maize Corn City of Madhya Pradesh."
            },
            "RABI": {
                "recommended_start": "10-15",
                "recommended_end": "11-25",
                "peak_period": "October 25 - November 10",
                "varieties": ["DKC-9108", "Bio-9681"],
                "notes": "Winter crop in river basins."
            }
        }
    },
    "madhya pradesh_dhar": {
        "state": "Madhya Pradesh",
        "district": "Dhar",
        "zone_key": "ZONE_8",
        "is_suitable": True,
        "soil_type": "Medium Deep Black Clay Loam",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-15",
                "recommended_end": "07-15",
                "peak_period": "June 20 - July 05",
                "varieties": ["JM-12", "JM-216", "Bio-9681"],
                "notes": "Malwa plateau Kharif maize."
            }
        }
    },

    # --- MAHARASHTRA ---
    "maharashtra_nashik": {
        "state": "Maharashtra",
        "district": "Nashik",
        "zone_key": "ZONE_9",
        "is_suitable": True,
        "soil_type": "Medium Black Soil to Loamy Basalt",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-15",
                "recommended_end": "07-20",
                "peak_period": "June 25 - July 08",
                "varieties": ["Rajarshi", "Karveer", "Pioneer 30R77", "Bio-9681"],
                "notes": "High silage and commercial grain output."
            },
            "RABI": {
                "recommended_start": "10-15",
                "recommended_end": "11-30",
                "peak_period": "November 01 - November 15",
                "varieties": ["Pioneer 30V92", "Bio-9681"],
                "notes": "Irrigated winter crop."
            }
        }
    },
    "maharashtra_aurangabad": {
        "state": "Maharashtra",
        "district": "Aurangabad",
        "zone_key": "ZONE_9",
        "is_suitable": True,
        "soil_type": "Deep Black Cotton Soil",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-15",
                "recommended_end": "07-15",
                "peak_period": "June 20 - July 05",
                "varieties": ["Bio-9681", "DKC-9108", "Karveer"],
                "notes": "Marathwada Kharif maize."
            },
            "RABI": {
                "recommended_start": "10-15",
                "recommended_end": "11-20",
                "peak_period": "October 25 - November 10",
                "varieties": ["Pioneer 30V92", "PAC-751"],
                "notes": "Rabi maize under drip."
            }
        }
    },
    "maharashtra_ratnagiri": {
        "state": "Maharashtra",
        "district": "Ratnagiri",
        "zone_key": "ZONE_12",
        "is_suitable": False,
        "unsuitable_reason": "High Konkan precipitation (>3000mm), coastal laterite soils prone to heavy leeching and root lodging.",
        "soil_type": "Konkan Laterite",
        "seasons": {}
    },

    # --- PUNJAB ---
    "punjab_ludhiana": {
        "state": "Punjab",
        "district": "Ludhiana",
        "zone_key": "ZONE_6",
        "is_suitable": True,
        "soil_type": "Alluvial Loamy Sand to Sandy Loam",
        "seasons": {
            "KHARIF": {
                "recommended_start": "05-20",
                "recommended_end": "06-30",
                "peak_period": "June 01 - June 15",
                "varieties": ["PMH-1", "PMH-3", "HQPM-5", "Bio-9637"],
                "notes": "Diversification crop from water-intensive paddy."
            },
            "SPRING": {
                "recommended_start": "01-20",
                "recommended_end": "02-28",
                "peak_period": "February 01 - February 15",
                "varieties": ["PMH-1", "Bio-9681", "P1844"],
                "notes": "High yield spring maize after potato/peas harvest."
            }
        }
    },
    "punjab_jalandhar": {
        "state": "Punjab",
        "district": "Jalandhar",
        "zone_key": "ZONE_6",
        "is_suitable": True,
        "soil_type": "Alluvial Silt Loam",
        "seasons": {
            "KHARIF": {
                "recommended_start": "05-25",
                "recommended_end": "06-30",
                "peak_period": "June 05 - June 20",
                "varieties": ["PMH-1", "PMH-3", "Pioneer 1844"],
                "notes": "Kharif grain and silage maize."
            },
            "SPRING": {
                "recommended_start": "01-25",
                "recommended_end": "02-28",
                "peak_period": "February 05 - February 20",
                "varieties": ["PMH-1", "Bio-9681"],
                "notes": "Spring maize."
            }
        }
    },

    # --- RAJASTHAN ---
    "rajasthan_bhilwara": {
        "state": "Rajasthan",
        "district": "Bhilwara",
        "zone_key": "ZONE_8",
        "is_suitable": True,
        "soil_type": "Mixed Red and Black Soil",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-20",
                "recommended_end": "07-15",
                "peak_period": "June 25 - July 05",
                "varieties": ["Mahi Kanchan", "Mahi Dhawal", "Pratap Makka 3", "Bio-9681"],
                "notes": "Mewar region staple Kharif crop."
            }
        }
    },
    "rajasthan_udaipur": {
        "state": "Rajasthan",
        "district": "Udaipur",
        "zone_key": "ZONE_8",
        "is_suitable": True,
        "soil_type": "Red and Medium Black Loam",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-20",
                "recommended_end": "07-20",
                "peak_period": "June 25 - July 08",
                "varieties": ["Mahi Kanchan", "Mahi Dhawal", "HQPM-1"],
                "notes": "Staple food crop in southern Rajasthan."
            }
        }
    },
    "rajasthan_jaisalmer": {
        "state": "Rajasthan",
        "district": "Jaisalmer",
        "zone_key": "ZONE_14",
        "is_suitable": False,
        "unsuitable_reason": "Hyper-arid desert environment, extreme thermal heat (>46°C), dry sandy dunes, acute water deficit.",
        "soil_type": "Desert Sand",
        "seasons": {}
    },
    "rajasthan_bikaner": {
        "state": "Rajasthan",
        "district": "Bikaner",
        "zone_key": "ZONE_14",
        "is_suitable": False,
        "unsuitable_reason": "Arid desert tract with high summer evapotranspiration and negligible moisture retention.",
        "soil_type": "Sandy Desert Soil",
        "seasons": {}
    },

    # --- UTTAR PRADESH ---
    "uttar pradesh_bulandshahr": {
        "state": "Uttar Pradesh",
        "district": "Bulandshahr",
        "zone_key": "ZONE_5",
        "is_suitable": True,
        "soil_type": "Fertile Gangetic Alluvial Loam",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-15",
                "recommended_end": "07-15",
                "peak_period": "June 20 - July 05",
                "varieties": ["Pusa HM-4", "Pusa HM-8", "Pusa HM-9", "Ganga-11"],
                "notes": "Western UP high-yield Kharif maize."
            },
            "SPRING": {
                "recommended_start": "02-01",
                "recommended_end": "03-05",
                "peak_period": "February 10 - February 25",
                "varieties": ["Bio-9681", "Pusa HM-4"],
                "notes": "Spring maize following sugarcane or potato."
            }
        }
    },
    "uttar pradesh_bahraich": {
        "state": "Uttar Pradesh",
        "district": "Bahraich",
        "zone_key": "ZONE_4",
        "is_suitable": True,
        "soil_type": "Tarai Alluvial Sandy Loam",
        "seasons": {
            "KHARIF": {
                "recommended_start": "06-10",
                "recommended_end": "07-15",
                "peak_period": "June 15 - June 30",
                "varieties": ["Shaktiman-1", "Ganga-11", "HQPM-1"],
                "notes": "Tarai belt Kharif crop."
            },
            "RABI": {
                "recommended_start": "10-20",
                "recommended_end": "11-30",
                "peak_period": "November 01 - November 15",
                "varieties": ["Shaktiman-2", "Bio-9681"],
                "notes": "Winter maize."
            }
        }
    },

    # --- ANDHRA PRADESH ---
    "andhra pradesh_guntur": {
        "state": "Andhra Pradesh",
        "district": "Guntur",
        "zone_key": "ZONE_11",
        "is_suitable": True,
        "soil_type": "Black Cotton Soil & Deltaic Alluvium",
        "seasons": {
            "RABI": {
                "recommended_start": "10-01",
                "recommended_end": "11-30",
                "peak_period": "October 15 - November 10",
                "varieties": ["DHM-117", "DKC-9108", "Bio-9681", "Pioneer 30V92"],
                "notes": "Zero-tillage maize after Kharif paddy."
            },
            "KHARIF": {
                "recommended_start": "06-01",
                "recommended_end": "07-15",
                "peak_period": "June 10 - June 25",
                "varieties": ["DHM-117", "NK-6240"],
                "notes": "Rainfed Kharif."
            }
        }
    }
}

# Taluka / Village Level Specific Overrides
TALUKA_VILLAGE_OVERRIDES = {
    "gujarat_panchmahal_godhra": {
        "taluka": "Godhra",
        "district": "Panchmahal",
        "state": "Gujarat",
        "is_suitable": True,
        "special_recommendation": "Main ICAR-Indian Institute of Maize Research regional zone. Excellent alluvial-loam tract.",
        "recommended_varieties": ["GAYMH-1", "GAWMH-2", "HQPM-1"]
    },
    "gujarat_panchmahal_halol": {
        "taluka": "Halol",
        "district": "Panchmahal",
        "state": "Gujarat",
        "is_suitable": True,
        "special_recommendation": "Pavagadh foothills tract. Heavy drainage recommended on slope bottoms.",
        "recommended_varieties": ["GAYMH-1", "Bio-9681"]
    },
    "bihar_begusarai_barauni": {
        "taluka": "Barauni",
        "district": "Begusarai",
        "state": "Bihar",
        "is_suitable": True,
        "special_recommendation": "Prime Gangetic diara and upland belt. Highly responsive to winter Nitrogen scheduling.",
        "recommended_varieties": ["Shaktiman-1", "DKC-9081", "Pioneer 30V92"]
    },
    "karnataka_davangere_harihar": {
        "taluka": "Harihar",
        "district": "Davangere",
        "state": "Karnataka",
        "is_suitable": True,
        "special_recommendation": "Tungabhadra river basin. Exceptional response to hybrid grain cultivation in Kharif & Rabi.",
        "recommended_varieties": ["DHM-117", "CP-818", "NK-6240"]
    },
    "rajasthan_jaisalmer_pokhran": {
        "taluka": "Pokhran",
        "district": "Jaisalmer",
        "state": "Rajasthan",
        "is_suitable": False,
        "unsuitable_reason": "Extreme arid desert microclimate, severe sand shifting, and brackish ground water.",
        "recommended_varieties": []
    }
}

# State-level default fallback definitions
STATE_MAIZE_DEFAULTS = {
    "Gujarat": {
        "zone_key": "ZONE_13",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("06-15", "07-20"), "RABI": ("10-15", "11-30"), "SUMMER": ("02-15", "03-15")},
        "soil_type": "Sandy Loam / Medium Black",
        "varieties": ["GAYMH-1", "GAWMH-2", "HQPM-1", "Bio-9681"]
    },
    "Bihar": {
        "zone_key": "ZONE_4",
        "is_suitable": True,
        "primary_season": "RABI",
        "default_sowing": {"RABI": ("10-15", "11-30"), "KHARIF": ("06-10", "07-15"), "SUMMER": ("02-01", "03-10")},
        "soil_type": "Gangetic Alluvial Loam",
        "varieties": ["Shaktiman-1", "Shaktiman-2", "DKC-9081", "HQPM-1"]
    },
    "Karnataka": {
        "zone_key": "ZONE_10",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("05-25", "07-15"), "RABI": ("09-15", "11-15"), "SUMMER": ("01-15", "02-28")},
        "soil_type": "Red Sandy Loam / Black Loam",
        "varieties": ["DHM-117", "CP-818", "NK-6240", "PAC-751"]
    },
    "Telangana": {
        "zone_key": "ZONE_10",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("06-01", "07-15"), "RABI": ("10-01", "11-20")},
        "soil_type": "Red Loam (Chalka) & Black Cotton",
        "varieties": ["DHM-117", "Bio-9681", "Pioneer 30V92"]
    },
    "Madhya Pradesh": {
        "zone_key": "ZONE_8",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("06-15", "07-15"), "RABI": ("10-15", "11-25")},
        "soil_type": "Medium Black / Mixed Red-Black",
        "varieties": ["JM-216", "Mahi Kanchan", "Bio-9681"]
    },
    "Maharashtra": {
        "zone_key": "ZONE_9",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("06-15", "07-20"), "RABI": ("10-15", "11-30")},
        "soil_type": "Medium Black Cotton Loam",
        "varieties": ["Rajarshi", "Karveer", "Bio-9681", "DKC-9108"]
    },
    "Punjab": {
        "zone_key": "ZONE_6",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("05-20", "06-30"), "SPRING": ("01-20", "02-28")},
        "soil_type": "Alluvial Loamy Sand",
        "varieties": ["PMH-1", "PMH-3", "HQPM-5"]
    },
    "Haryana": {
        "zone_key": "ZONE_6",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("05-25", "06-30"), "SPRING": ("01-25", "02-28")},
        "soil_type": "Alluvial Loam",
        "varieties": ["PMH-1", "HQPM-1", "Bio-9681"]
    },
    "Uttar Pradesh": {
        "zone_key": "ZONE_5",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("06-15", "07-15"), "RABI": ("10-20", "11-30"), "SPRING": ("02-01", "03-05")},
        "soil_type": "Alluvial Silt Loam",
        "varieties": ["Pusa HM-4", "Pusa HM-8", "Ganga-11"]
    },
    "Rajasthan": {
        "zone_key": "ZONE_8",
        "is_suitable": True,
        "primary_season": "KHARIF",
        "default_sowing": {"KHARIF": ("06-20", "07-20")},
        "soil_type": "Mixed Red-Black & Sandy Loam",
        "varieties": ["Mahi Kanchan", "Mahi Dhawal", "Pratap Makka 3"]
    },
    "Andhra Pradesh": {
        "zone_key": "ZONE_11",
        "is_suitable": True,
        "primary_season": "RABI",
        "default_sowing": {"RABI": ("10-01", "11-30"), "KHARIF": ("06-01", "07-15")},
        "soil_type": "Black Cotton & Coastal Alluvium",
        "varieties": ["DHM-117", "DKC-9108", "Bio-9681"]
    },
    "Kerala": {
        "zone_key": "ZONE_12",
        "is_suitable": False,
        "unsuitable_reason": "Excessive monsoon precipitation (>3000mm) and acidic laterite soils cause severe fungal root rot and grain spoilage.",
        "soil_type": "Acid Laterite",
        "varieties": []
    },
    "Goa": {
        "zone_key": "ZONE_12",
        "is_suitable": False,
        "unsuitable_reason": "High coastal rainfall and humidity unsuitable for commercial maize grain filling.",
        "soil_type": "Coastal Laterite",
        "varieties": []
    }
}

# National Fallback Configuration (Priority Level 5)
NATIONAL_FALLBACK_MAIZE = {
    "crop": "MAIZE",
    "botanical_name": "Zea mays L.",
    "is_suitable": True,
    "primary_season": "KHARIF",
    "seasons": {
        "KHARIF": {
            "recommended_start": "06-15",
            "recommended_end": "07-15",
            "peak_period": "June 25 - July 05",
            "varieties": ["HQPM-1", "Bio-9681", "Ganga-11", "PAC-751"]
        },
        "RABI": {
            "recommended_start": "10-15",
            "recommended_end": "11-25",
            "peak_period": "November 01 - November 15",
            "varieties": ["DKC-9108", "Bio-9681", "Pioneer 30V92"]
        },
        "SUMMER": {
            "recommended_start": "02-01",
            "recommended_end": "03-05",
            "peak_period": "February 15 - February 25",
            "varieties": ["DKC-9081", "PAC-751"]
        },
        "SPRING": {
            "recommended_start": "01-20",
            "recommended_end": "02-28",
            "peak_period": "February 01 - February 15",
            "varieties": ["PMH-1", "Bio-9681"]
        }
    },
    "optimal_soil": "Well-drained deep loamy soil rich in organic matter (pH 5.8 to 7.5)",
    "water_requirement_mm": "500 - 800 mm evenly distributed",
    "temperature_range_c": "18°C - 35°C"
}
