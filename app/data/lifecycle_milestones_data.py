"""
12-Week Indian Maize Crop Lifecycle Roadmap & Milestones Database
Defines weekly phenological stages, mandatory scan checkpoints, key scouting targets,
fertigation operations, and proactive reminder templates.
"""

LIFECYCLE_MILESTONES = [
    {
        "week_number": 1,
        "das_start": 0,
        "das_end": 7,
        "growth_stage": "VE",
        "stage_title": "Germination & Coleoptile Emergence",
        "scan_target": "Scan #1 (DAS 7) - Seedling Emergence Uniformity",
        "scouting_checklist": [
            "Check for uniform 85%+ germination across field rows",
            "Scout for cutworms clipping young coleoptiles at soil level",
            "Check for hard soil surface crusting after light monsoon showers"
        ],
        "agronomic_operations": "Apply pre-emergence herbicide (Atrazine 50% WP @ 1 kg/ha) within 48h of sowing. Maintain light germination moisture.",
        "reminder_copy": "🌱 Week 1: Check germination! Take Scan #1 of your seedlings to verify uniform emergence.",
        "urgency": "NORMAL",
        "critical_window": False
    },
    {
        "week_number": 2,
        "das_start": 8,
        "das_end": 14,
        "growth_stage": "V1 - V2",
        "stage_title": "First Leaf Collar Emergence & Seedling Vigor",
        "scan_target": "Scan #2 (DAS 14) - Seedling Vigor & Early Weed Competition",
        "scouting_checklist": [
            "Inspect for Downy Mildew systemic chlorotic leaf striping",
            "Check for seedling damping-off (Pythium / Rhizoctonia)",
            "Thin out crowded seedlings to maintain 20 cm spacing between plants"
        ],
        "agronomic_operations": "Rogue out stunted or albino infected seedlings. Perform first hand-weeding.",
        "reminder_copy": "🌿 Week 2: Inspect seedlings. Take Scan #2 to check early vigor and weed competition.",
        "urgency": "NORMAL",
        "critical_window": False
    },
    {
        "week_number": 3,
        "das_start": 15,
        "das_end": 21,
        "growth_stage": "V3 - V4",
        "stage_title": "Nodal Root Initiation & Rapid Vegetative Surge",
        "scan_target": "Scan #3 (DAS 21) - Whorl Health & Nitrogen Baseline",
        "scouting_checklist": [
            "Inspect central whorls for early pinhole chewing damage",
            "Check for V-shaped yellowing along midrib indicating Nitrogen deficiency",
            "Scout for early Fall Armyworm (FAW) egg masses on lower leaf surfaces"
        ],
        "agronomic_operations": "1st Split Nitrogen Top-Dressing: Apply 30% of total Urea side-banded 5 cm away from rows.",
        "reminder_copy": "⚡ Week 3: Time for Scan #3 & 1st Urea top-dressing! Inspect young whorls for early borer signs.",
        "urgency": "MEDIUM",
        "critical_window": False
    },
    {
        "week_number": 4,
        "das_start": 22,
        "das_end": 28,
        "growth_stage": "V5 - V6",
        "stage_title": "Growing Point Elevation & Tassel Differentiation",
        "scan_target": "Scan #4 (DAS 28) - Fall Armyworm & Stem Borer Screening",
        "scouting_checklist": [
            "Scout for sawdust-like frass inside whorls caused by Fall Armyworm",
            "Look for dead hearts and shot holes caused by Chilo stem borers",
            "Check for Zinc deficiency broad white/bleached bands on young leaves"
        ],
        "agronomic_operations": "If FAW whorl damage > 10%: Apply Emamectin Benzoate 5% SG (0.4 g/L) or Chlorantraniliprole 18.5% SC (0.4 ml/L) directly into whorls.",
        "reminder_copy": "🐛 Week 4 Critical: Scout whorls! Upload Scan #4 to screen for Fall Armyworm and stem borers.",
        "urgency": "HIGH",
        "critical_window": True
    },
    {
        "week_number": 5,
        "das_start": 29,
        "das_end": 35,
        "growth_stage": "V7 - V8",
        "stage_title": "Rapid Stalk Elongation & Canopy Closure",
        "scan_target": "Scan #5 (DAS 35) - Stalk Surge & Lower Leaf BLSB Check",
        "scouting_checklist": [
            "Inspect lower leaf sheaths for water-soaked lesions (Banded Leaf & Sheath Blight)",
            "Measure stalk height progress (expected 50 - 80 cm)",
            "Check for soil moisture adequacy as canopy closes"
        ],
        "agronomic_operations": "Strip bottom 2-3 older leaves touching wet soil to arrest BLSB fungal spread. Maintain good drainage.",
        "reminder_copy": "📏 Week 5: Rapid growth phase! Take Scan #5 to measure stalk elongation and inspect lower leaf sheaths.",
        "urgency": "MEDIUM",
        "critical_window": False
    },
    {
        "week_number": 6,
        "das_start": 36,
        "das_end": 42,
        "growth_stage": "V9 - V10",
        "stage_title": "Brace Root Anchoring & Pre-Tasseling Development",
        "scan_target": "Scan #6 (DAS 42) - Pre-Tasseling Stalk Integrity & Rust Check",
        "scouting_checklist": [
            "Check for Common Rust cinnamon-brown pustules on both leaf surfaces",
            "Inspect lower stalk nodes for stem borer tunnel entry holes",
            "Check for brace root emergence from lower 2 stalk nodes"
        ],
        "agronomic_operations": "2nd Split Nitrogen: Apply 40% of total Urea. Earth-up soil around plant base to prevent wind lodging.",
        "reminder_copy": "🌾 Week 6: Apply 2nd Urea dose & earth-up soil! Upload Scan #6 for pre-tasseling height check.",
        "urgency": "HIGH",
        "critical_window": False
    },
    {
        "week_number": 7,
        "das_start": 43,
        "das_end": 50,
        "growth_stage": "VT",
        "stage_title": "Tassel Emergence (Peak Water & Heat Sensitivity)",
        "scan_target": "Scan #7 (DAS 49) - Tassel Health & Foliar Blight Surveillance",
        "scouting_checklist": [
            "Check tassel emergence and pollen shed vitality",
            "Inspect for Turcicum Leaf Blight cigar-shaped necrotic lesions",
            "Monitor soil moisture tension—drought now causes severe yield loss"
        ],
        "agronomic_operations": "CRITICAL WATER WINDOW #1: Ensure optimal soil moisture (ETc = 1.15 x ET0). Yield drops 3-4%/day during moisture stress.",
        "reminder_copy": "💧 Week 7 Alert: Tasseling started! Moisture stress now cuts yield by 3-4%/day. Ensure timely irrigation & Scan #7.",
        "urgency": "CRITICAL",
        "critical_window": True
    },
    {
        "week_number": 8,
        "das_start": 51,
        "das_end": 60,
        "growth_stage": "R1",
        "stage_title": "Silking, Ovule Pollination & Ear Formation",
        "scan_target": "Scan #8 (DAS 56) - Silk Vigor & Ear Pathology Screening",
        "scouting_checklist": [
            "Check for silk clipping beetles or earworms eating fresh silks",
            "Inspect for Fusarium molds or pinkish fungal growth at ear tip",
            "Verify complete silk pollination coverage"
        ],
        "agronomic_operations": "CRITICAL WATER WINDOW #2: Maintain steady irrigation. If fungal blight is active, apply Propiconazole 25% EC @ 1 ml/L.",
        "reminder_copy": "🌽 Week 8: Silking & Pollination! Upload Scan #8 of emerging silks and cobs to verify grain set.",
        "urgency": "CRITICAL",
        "critical_window": True
    },
    {
        "week_number": 9,
        "das_start": 61,
        "das_end": 70,
        "growth_stage": "R2",
        "stage_title": "Blister Stage & Rapid Endosperm Expansion",
        "scan_target": "Scan #9 (DAS 65) - Cob Development & Earworm Inspection",
        "scouting_checklist": [
            "Check kernel blister filling and watery endosperm development",
            "Inspect cob tip for Corn Earworm / Cob Worm entry holes",
            "Scout upper canopy leaves for leaf spot coalescence"
        ],
        "agronomic_operations": "Maintain consistent soil moisture to prevent kernel abortion at cob tip.",
        "reminder_copy": "✨ Week 9: Kernels entering blister stage. Take Scan #9 to evaluate cob filling and pest protection.",
        "urgency": "MEDIUM",
        "critical_window": False
    },
    {
        "week_number": 10,
        "das_start": 71,
        "das_end": 80,
        "growth_stage": "R3",
        "stage_title": "Milk Stage & Starch Accumulation",
        "scan_target": "Scan #10 (DAS 75) - Starch Fill & Late Rust Guard",
        "scouting_checklist": [
            "Inspect kernels—milky white fluid turning into light starch",
            "Check that ear leaves remain green and photosynthetically active",
            "Scout for late Turcicum blight creeping onto upper canopy"
        ],
        "agronomic_operations": "Apply final light irrigation if soil moisture is below 50% available water capacity.",
        "reminder_copy": "🥛 Week 10: Milk stage kernel fill. Upload Scan #10 to safeguard upper canopy foliage until grain maturity.",
        "urgency": "MEDIUM",
        "critical_window": False
    },
    {
        "week_number": 11,
        "das_start": 81,
        "das_end": 95,
        "growth_stage": "R4 - R5",
        "stage_title": "Dough Stage, Dent Formation & Starch Hardening",
        "scan_target": "Scan #11 (DAS 85) - Starch Line Movement & Husk Senescence",
        "scouting_checklist": [
            "Check for husk leaves turning from emerald green to pale straw yellow",
            "Track starch line moving from kernel crown to kernel base",
            "Inspect lower stalk strength—check for Fusarium stalk rot softening"
        ],
        "agronomic_operations": "Taper off irrigation to facilitate field drying. Observe chemical Pre-Harvest Interval (PHI) limits.",
        "reminder_copy": "🌾 Week 11: Dough stage. Husks turning straw-yellow. Stop chemical sprays & take Scan #11.",
        "urgency": "LOW",
        "critical_window": False
    },
    {
        "week_number": 12,
        "das_start": 96,
        "das_end": 120,
        "growth_stage": "R6",
        "stage_title": "Black Layer Formation & Harvest Readiness",
        "scan_target": "Scan #12 (DAS 105) - Harvest Readiness & Grain Moisture Check",
        "scouting_checklist": [
            "Extract test kernels—verify black abscission layer at kernel tip",
            "Check cob droop and grain moisture (target 15 - 20% for harvest)",
            "Verify all chemical PHI withholding intervals have expired"
        ],
        "agronomic_operations": "Harvest Green Light: Harvest in dry weather. Sun-dry grains on tarpaulin until moisture < 12% before storage.",
        "reminder_copy": "🎉 🌾 Week 12: Crop fully matured! Your field is ready for harvest. Check optimal harvesting guidance.",
        "urgency": "CRITICAL",
        "critical_window": True
    }
]
