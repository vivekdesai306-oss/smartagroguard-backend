"""
Multi-Temporal Treatment Efficacy & Lesion Recovery Tracking Service
Compares pre-spray vs post-spray scans to compute necrotic area reduction and healing rate.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

class TreatmentEfficacyService:
    @staticmethod
    def compare_treatment_efficacy(
        pre_scan: Dict[str, Any],
        post_scan: Dict[str, Any],
        applied_chemical: Optional[str] = "Propiconazole 25% EC"
    ) -> Dict[str, Any]:
        """
        Computes % foliar lesion reduction across multi-temporal scans.
        Efficacy (%) = ((Severity_T0 - Severity_T10) / Severity_T0) * 100
        """
        pre_disease = pre_scan.get("disease_analysis", {}).get("detected_disease", "Northern Leaf Blight")
        post_disease = post_scan.get("disease_analysis", {}).get("detected_disease", "Healthy")
        
        pre_ratio = pre_scan.get("disease_analysis", {}).get("affected_area_ratio", 0.15)
        post_ratio = post_scan.get("disease_analysis", {}).get("affected_area_ratio", 0.03)

        if post_disease.lower() == "healthy":
            post_ratio = 0.0

        if pre_ratio <= 0.001:
            efficacy_pct = 100.0 if post_ratio == 0.0 else 0.0
        else:
            reduction = max(0.0, pre_ratio - post_ratio)
            efficacy_pct = round((reduction / pre_ratio) * 100.0, 1)

        # Classify Efficacy Tier
        if efficacy_pct >= 75.0:
            rating = "HIGHLY_EFFECTIVE"
            headline = f"✓ High Treatment Response ({efficacy_pct}% Lesion Reduction)"
            advisory = f"The applied {applied_chemical} successfully arrested pathogen expansion. Lesions are desiccated and non-sporulating. Continue standard crop care."
        elif efficacy_pct >= 40.0:
            rating = "MODERATE_RESPONSE"
            headline = f"⚠ Moderate Treatment Response ({efficacy_pct}% Lesion Reduction)"
            advisory = f"Partial fungal lesion arrest observed. If humid weather persists, consider a follow-up rotation spray with an alternate chemical group."
        else:
            rating = "POOR_OR_RESISTANT"
            headline = f"❌ Low Treatment Response ({efficacy_pct}% Lesion Reduction)"
            advisory = f"Pathogen progression continues despite {applied_chemical}. Rotate immediately to an alternate active ingredient (e.g., Azoxystrobin + Difenoconazole) to prevent fungicide resistance."

        return {
            "applied_chemical": applied_chemical,
            "pre_scan_id": pre_scan.get("scan_id", "SCAN_PRE"),
            "pre_scan_disease": pre_disease,
            "pre_scan_affected_ratio": pre_ratio,
            "post_scan_id": post_scan.get("scan_id", "SCAN_POST"),
            "post_scan_disease": post_disease,
            "post_scan_affected_ratio": post_ratio,
            "lesion_reduction_pct": efficacy_pct,
            "efficacy_rating": rating,
            "headline": headline,
            "clinical_advisory": advisory
        }
