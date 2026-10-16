"""
Pest Vector Linkage & Secondary Infection Correlation Engine
Correlates observed insect wound entry and pest presence with elevated fungal/bacterial rot risks.
"""
from typing import Dict, Any, List, Optional
from ..data.pest_vector_data import PEST_VECTOR_DATABASE, NUTRIENT_DEFICIENCY_DATABASE

class PestVectorEngine:
    @staticmethod
    def evaluate_vector_risk(
        observed_pests: List[str] = [],
        observed_symptoms: List[str] = [],
        has_whorl_damage: bool = False,
        has_stem_holes: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates secondary pathology vulnerability triggered by insect vectors.
        """
        elevated_risks = []
        action_recommendations = []
        vector_matches = []

        if "FALL_ARMYWORM" in observed_pests or has_whorl_damage or "frass" in [s.lower() for s in observed_symptoms]:
            faw = PEST_VECTOR_DATABASE["FALL_ARMYWORM"]
            vector_matches.append(faw)
            elevated_risks.append({
                "pest": "Fall Armyworm (Spodoptera frugiperda)",
                "secondary_diseases": faw["correlated_diseases"],
                "mechanism": faw["wound_to_disease_mechanism"],
                "risk_multiplier": faw["risk_multiplier"]
            })
            action_recommendations.append(faw["recommended_control"])

        if "STEM_BORER" in observed_pests or has_stem_holes or "dead_heart" in [s.lower() for s in observed_symptoms]:
            borer = PEST_VECTOR_DATABASE["SPOTTED_STEM_BORER"]
            vector_matches.append(borer)
            elevated_risks.append({
                "pest": "Spotted Stem Borer (Chilo partellus)",
                "secondary_diseases": borer["correlated_diseases"],
                "mechanism": borer["wound_to_disease_mechanism"],
                "risk_multiplier": borer["risk_multiplier"]
            })
            action_recommendations.append(borer["recommended_control"])

        if "APHIDS" in observed_pests or "honeydew" in [s.lower() for s in observed_symptoms]:
            aphid = PEST_VECTOR_DATABASE["CORN_LEAF_APHID"]
            vector_matches.append(aphid)
            elevated_risks.append({
                "pest": "Corn Leaf Aphid (Rhopalosiphum maidis)",
                "secondary_diseases": aphid["correlated_diseases"],
                "mechanism": aphid["wound_to_disease_mechanism"],
                "risk_multiplier": aphid["risk_multiplier"]
            })
            action_recommendations.append(aphid["recommended_control"])

        is_vector_active = len(vector_matches) > 0
        headline = "⚠ Secondary Infection Gateway Detected: Insect Wounds Open Entry for Stalk & Ear Rots" if is_vector_active else "✓ Zero Vector Infestation Detected"

        return {
            "has_vector_activity": is_vector_active,
            "headline": headline,
            "detected_vectors": [v["scientific_name"] for v in vector_matches],
            "elevated_disease_risks": elevated_risks,
            "vector_control_measures": action_recommendations
        }

    @staticmethod
    def get_nutrient_deficiency_profile(deficiency_id: str) -> Optional[Dict[str, Any]]:
        return NUTRIENT_DEFICIENCY_DATABASE.get(deficiency_id)
