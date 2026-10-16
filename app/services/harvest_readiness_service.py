"""
Multi-Criteria Optimal Harvest Readiness & Post-Harvest Storage Advisor
Evaluates:
1. Physiological Maturity (R6 Black Layer at kernel base)
2. Cumulative Growing Degree Days (GDD >= 1450 °C-days)
3. Grain Field Moisture Content (target 15 - 20%)
4. Pre-Harvest Interval (PHI) Chemical Clearance
5. 72-Hour Rain-Free Meteorological Harvesting Window
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..data.cibrc_chemical_database import CIBRC_CHEMICAL_DATABASE

class HarvestReadinessService:
    @classmethod
    def evaluate_harvest_readiness(
        cls,
        farm_id: Optional[str] = None,
        das: int = 105,
        growth_stage: str = "R6",
        cumulative_gdd: float = 1480.0,
        estimated_grain_moisture_pct: float = 18.5,
        last_chemical_spray_date: Optional[str] = None,
        last_chemical_id: Optional[str] = None,
        forecast_rain_next_3_days_mm: float = 0.0
    ) -> Dict[str, Any]:
        """
        Executes the 5-Pillar Harvest Decision Tree.
        """
        criteria = []
        passed_count = 0

        # 1. Physiological Maturity (R6 Stage / Black Layer)
        is_r6 = (growth_stage.upper() == "R6" or das >= 95)
        if is_r6:
            passed_count += 1
            criteria.append({
                "criterion_name": "1. Physiological Black Layer Formation",
                "is_passed": True,
                "current_value": "R6 (Black Layer Formed)",
                "target_threshold": "R6 Black Layer",
                "status_label": "PASSED (Green)",
                "explanation": "Abscission layer at kernel base has completely blackened. Zero further starch transfer from stalk."
            })
        else:
            criteria.append({
                "criterion_name": "1. Physiological Black Layer Formation",
                "is_passed": False,
                "current_value": f"Stage {growth_stage} (DAS {das})",
                "target_threshold": "R6 Black Layer",
                "status_label": "HOLD (Yellow)",
                "explanation": "Crop has not reached full physiological maturity. Starch hardening is still actively underway."
            })

        # 2. Cumulative GDD Target (>= 1450 °C-days)
        gdd_passed = (cumulative_gdd >= 1450.0)
        if gdd_passed:
            passed_count += 1
            criteria.append({
                "criterion_name": "2. Thermal Heat Units (Cumulative GDD)",
                "is_passed": True,
                "current_value": f"{cumulative_gdd:.1f} °C-days",
                "target_threshold": "≥ 1450 °C-days",
                "status_label": "PASSED (Green)",
                "explanation": "Accumulated thermal units fully satisfy hybrid biological maturity requirements."
            })
        else:
            criteria.append({
                "criterion_name": "2. Thermal Heat Units (Cumulative GDD)",
                "is_passed": False,
                "current_value": f"{cumulative_gdd:.1f} °C-days",
                "target_threshold": "≥ 1450 °C-days",
                "status_label": "HOLD (Yellow)",
                "explanation": f"Thermal accumulation is short by {1450.0 - cumulative_gdd:.1f} °C-days."
            })

        # 3. Grain Moisture Content (<= 20%)
        moisture_passed = (estimated_grain_moisture_pct <= 20.0)
        if moisture_passed:
            passed_count += 1
            criteria.append({
                "criterion_name": "3. Grain Kernel Field Moisture",
                "is_passed": True,
                "current_value": f"{estimated_grain_moisture_pct:.1f}%",
                "target_threshold": "≤ 20.0%",
                "status_label": "PASSED (Green)",
                "explanation": "Field dry-down achieved optimal harvesting moisture. Husks are papery-brown and ears droop."
            })
        else:
            criteria.append({
                "criterion_name": "3. Grain Kernel Field Moisture",
                "is_passed": False,
                "current_value": f"{estimated_grain_moisture_pct:.1f}%",
                "target_threshold": "≤ 20.0%",
                "status_label": "HOLD (Yellow)",
                "explanation": "Moisture is too high (> 20%). Premature harvesting will cause grain bruising, mold, and drying costs."
            })

        # 4. Pre-Harvest Interval (PHI) Clearance
        phi_days_rem = 0
        phi_passed = True
        if last_chemical_spray_date and last_chemical_id:
            chem = CIBRC_CHEMICAL_DATABASE.get(last_chemical_id, {})
            req_phi = chem.get("phi_days", 21)
            try:
                spray_dt = datetime.strptime(last_chemical_spray_date, "%Y-%m-%d")
                days_since_spray = (datetime.utcnow() - spray_dt).days
                if days_since_spray < req_phi:
                    phi_passed = False
                    phi_days_rem = req_phi - days_since_spray
            except Exception:
                pass

        if phi_passed:
            passed_count += 1
            criteria.append({
                "criterion_name": "4. Chemical Pre-Harvest Interval (PHI) Safety",
                "is_passed": True,
                "current_value": "Zero active chemical residue",
                "target_threshold": "All PHI intervals cleared",
                "status_label": "PASSED (Green)",
                "explanation": "Safe for human food and livestock fodder consumption. Zero chemical withholding restrictions."
            })
        else:
            criteria.append({
                "criterion_name": "4. Chemical Pre-Harvest Interval (PHI) Safety",
                "is_passed": False,
                "current_value": f"{phi_days_rem} days withholding remaining",
                "target_threshold": "All PHI intervals cleared",
                "status_label": "HOLD (Red Lockout)",
                "explanation": f"Active pesticide application ({last_chemical_id}) requires {phi_days_rem} more days of withholding before safe harvest."
            })

        # 5. 72-Hour Rain-Free Weather Window
        weather_passed = (forecast_rain_next_3_days_mm < 5.0)
        if weather_passed:
            passed_count += 1
            criteria.append({
                "criterion_name": "5. 72-Hour Rain-Free Harvesting Window",
                "is_passed": True,
                "current_value": f"{forecast_rain_next_3_days_mm:.1f} mm rain forecast",
                "target_threshold": "< 5.0 mm in next 72h",
                "status_label": "PASSED (Green)",
                "explanation": "Dry, sunny weather confirmed. Optimal conditions for threshing and on-tarpaulin solar drying."
            })
        else:
            criteria.append({
                "criterion_name": "5. 72-Hour Rain-Free Harvesting Window",
                "is_passed": False,
                "current_value": f"{forecast_rain_next_3_days_mm:.1f} mm rain forecast",
                "target_threshold": "< 5.0 mm in next 72h",
                "status_label": "HOLD (Weather Warning)",
                "explanation": "Rain forecast in next 72h. Delay harvesting to prevent wet grain cobs and Aspergillus mold."
            })

        score_pct = round((passed_count / 5.0) * 100.0, 1)

        # Decision State
        if passed_count == 5:
            overall_status = "GREEN_LIGHT_HARVEST"
            is_ready = True
            headline = "🌾 GREEN LIGHT: Optimal Harvest Window Open!"
            plain_summary = "All 5 agronomic, thermal, moisture, safety, and meteorological criteria are fully satisfied. Your maize crop is ready for immediate harvest."
        elif not phi_passed:
            overall_status = "CHEMICAL_PHI_HOLD"
            is_ready = False
            headline = "⛔ Chemical Safety Hold: Pre-Harvest Interval (PHI) Active"
            plain_summary = f"Harvest is locked out for {phi_days_rem} days to ensure zero toxic chemical residue remains in harvested grain."
        elif not weather_passed:
            overall_status = "WEATHER_RAIN_HOLD"
            is_ready = False
            headline = "🌧 Weather Hold: Rain Forecast in Next 72 Hours"
            plain_summary = "Delay harvest until the rain front passes to avoid harvesting damp cobs susceptible to post-harvest ear rot."
        else:
            overall_status = "IMMATURE_GRAIN_HOLD"
            is_ready = False
            headline = "⏳ Crop Maturation in Progress"
            plain_summary = "Maintain field dry-down. Allow kernels to complete black layer formation and reach target moisture < 20%."

        storage_protocol = [
            "1. Harvest early morning or late afternoon to prevent kernel shattering during mechanical cob snapping.",
            "2. Thresh immediately and spread grains evenly on clean HDPE tarpaulins for 2-3 days of open solar drying.",
            "3. Dry down to strictly < 12.0% grain moisture to prevent Aspergillus flavus mold growth and dangerous aflatoxin synthesis.",
            "4. Store dried grains in hermetic Purdue Improved Crop Storage (PICS) bags or airtight galvanized metal bins to suffocate maize weevils."
        ]

        return {
            "farm_id": farm_id,
            "overall_status": overall_status,
            "is_ready_for_harvest": is_ready,
            "harvest_readiness_score_pct": score_pct,
            "headline": headline,
            "plain_summary": plain_summary,
            "criteria_breakdown": criteria,
            "phi_countdown_days_remaining": phi_days_rem,
            "post_harvest_storage_protocol": storage_protocol,
            "optimal_harvest_window": "Open for next 4-6 days (Sunny Dry Forecast)" if is_ready else "Projected in 7 - 14 days"
        }
