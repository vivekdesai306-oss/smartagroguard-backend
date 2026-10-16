"""
Pest Vector Linkages, Secondary Rot Correlations, and Nutrient Deficiency Database
Target Crop: Hybrid Maize (Zea mays L.)
"""

PEST_VECTOR_DATABASE = {
    "FALL_ARMYWORM": {
        "pest_id": "FALL_ARMYWORM",
        "scientific_name": "Spodoptera frugiperda",
        "vernacular_name": "Khabra / Katarpillar / Sanya",
        "feeding_type": "Whorl & Ear Chewing",
        "visual_indicators": ["Coarse sawdust-like frass in whorl", "Windowpaning and ragged holes in leaves", "Cob tip tunneling"],
        "correlated_diseases": ["Fusarium Stalk & Ear Rot", "Aspergillus Ear Rot / Aflatoxin", "Banded Leaf & Sheath Blight (BLSB)"],
        "wound_to_disease_mechanism": "Larval chewing penetrates stalk rind and cob husks, breaking the protective cuticle and inoculating airborne Fusarium verticillioides spores.",
        "risk_multiplier": 2.5,
        "recommended_control": "Apply Emamectin Benzoate 5% SG @ 0.4 g/L or Chlorantraniliprole 18.5% SC @ 0.4 ml/L directed into whorls."
    },
    "SPOTTED_STEM_BORER": {
        "pest_id": "SPOTTED_STEM_BORER",
        "scientific_name": "Chilo partellus",
        "vernacular_name": "Dankh / Gaabno Kido",
        "feeding_type": "Stalk Tunneling & Central Shoot Chewing",
        "visual_indicators": ["Dead heart in young plants", "Shot holes in leaf whorls", "Entry holes with frass on lower stem internodes"],
        "correlated_diseases": ["Bacterial Stalk Rot (Dickeya zeae)", "Anthracnose Stalk Rot", "Fusarium Stalk Rot"],
        "wound_to_disease_mechanism": "Tunneling creates open water-logged entry channels for soil and rain-borne Dickeya zeae bacteria to cause internal vascular collapse.",
        "risk_multiplier": 3.0,
        "recommended_control": "Apply Carbofuran 3G granules or spray Chlorantraniliprole 18.5% SC. Ensure soil drainage to prevent bacterial rot."
    },
    "CORN_LEAF_APHID": {
        "pest_id": "CORN_LEAF_APHID",
        "scientific_name": "Rhopalosiphum maidis",
        "vernacular_name": "Molo-Mashi / Aphids",
        "feeding_type": "Sap Sucking (Vector)",
        "visual_indicators": ["Dense colonies in upper whorl and tassel", "Sticky honeydew and black sooty mold", "Leaf curling and stunting"],
        "correlated_diseases": ["Maize Dwarf Mosaic Virus (MDMV)", "Sugarcane Mosaic Virus (SCMV)"],
        "wound_to_disease_mechanism": "Stylet penetration acts as an exclusive transmission vector for Potyviruses, causing systemic light green/yellow mosaic mottling.",
        "risk_multiplier": 2.2,
        "recommended_control": "Spray Imidacloprid 17.8% SL @ 0.3 ml/L or Neem Oil (10,000 ppm) @ 3 ml/L to eliminate vector populations."
    }
}

NUTRIENT_DEFICIENCY_DATABASE = {
    "NITROGEN_DEFICIENCY": {
        "deficiency_id": "NITROGEN_DEFICIENCY",
        "nutrient": "Nitrogen (N)",
        "symptoms": "V-shaped chlorosis (yellowing) starting at leaf tip and progressing along the midrib on older lower leaves. Plant exhibits stunted, pale yellowish green appearance.",
        "differentiated_from_fungal": "Fungal blights produce irregular or elliptical lesions with dark necrotic borders; Nitrogen deficiency strictly produces symmetrical V-shaped chlorosis along the midrib on older leaves.",
        "remediation": "Apply split dose of Urea (40 - 50 kg/ha) side-dressed 5 cm from rows before irrigation."
    },
    "POTASSIUM_DEFICIENCY": {
        "deficiency_id": "POTASSIUM_DEFICIENCY",
        "nutrient": "Potassium (K)",
        "symptoms": "Marginal scorching and necrosis along the outer edges of lower leaves. Midrib remains green.",
        "differentiated_from_fungal": "Affects leaf margins continuously without concentric ring patterns characteristic of fungal lesions.",
        "remediation": "Apply Muriate of Potash (MOP / KCl @ 30 - 40 kg/ha) or foliar spray of Potassium Nitrate (13-0-45 @ 10 g/L)."
    },
    "ZINC_DEFICIENCY": {
        "deficiency_id": "ZINC_DEFICIENCY",
        "nutrient": "Zinc (Zn)",
        "symptoms": "Broad bleached or white/yellow bands on either side of the midrib on upper young leaves ('White Bud' in maize). Midrib and outer margins remain green.",
        "differentiated_from_fungal": "Symmetrical longitudinal bands on emerging leaves without fungal pustules or necrotic spore centers.",
        "remediation": "Foliar application of Zinc Sulphate (ZnSO4 21% @ 5 g/L + 2.5 g/L Lime) or soil application of 25 kg/ha ZnSO4 at sowing."
    }
}
