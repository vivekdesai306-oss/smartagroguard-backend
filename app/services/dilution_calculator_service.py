"""
Knapsack Sprayer Tank Dilution & CIBRC Chemical Dosage Engine
Calculates exact chemical volume, tank batch quantities, water volume, and PHI compliance.
"""
import math
from typing import Dict, Any, List
from ..data.cibrc_chemical_database import CIBRC_CHEMICAL_DATABASE

class DilutionCalculatorService:
    @staticmethod
    def calculate_knapsack_dilution(
        chemical_id: str,
        area_acres: float = 1.0,
        tank_capacity_liters: float = 15.0,
        water_volume_per_acre_liters: float = 200.0
    ) -> Dict[str, Any]:
        """
        Calculates precision batching for 15L or 20L knapsack sprayer tanks.
        """
        chem = CIBRC_CHEMICAL_DATABASE.get(chemical_id)
        if not chem:
            # Fallback to Propiconazole default
            chem = CIBRC_CHEMICAL_DATABASE["PROPICONAZOLE_25_EC"]
            chemical_id = "PROPICONAZOLE_25_EC"

        total_water_liters = round(area_acres * water_volume_per_acre_liters, 1)
        total_tanks = math.ceil(total_water_liters / tank_capacity_liters)
        if total_tanks == 0:
            total_tanks = 1

        rate_per_liter = chem["rate_ml_per_liter"]
        chem_per_tank = round(rate_per_liter * tank_capacity_liters, 1)
        unit = chem["unit"]
        total_chemical_needed = round(rate_per_liter * total_water_liters, 1)

        # Generate step-by-step batching instructions
        batch_instructions = []
        for tank_idx in range(1, total_tanks + 1):
            is_last = (tank_idx == total_tanks)
            # If last tank has less remaining water
            water_in_tank = tank_capacity_liters
            chem_in_tank = chem_per_tank
            if is_last:
                rem_water = total_water_liters - ((total_tanks - 1) * tank_capacity_liters)
                if rem_water > 0 and rem_water < tank_capacity_liters:
                    water_in_tank = round(rem_water, 1)
                    chem_in_tank = round(rate_per_liter * rem_water, 1)

            batch_instructions.append({
                "tank_number": tank_idx,
                "water_liters": water_in_tank,
                "chemical_amount": chem_in_tank,
                "unit": unit,
                "action_instruction": f"Fill tank with {water_in_tank}L clean water, measure exactly {chem_in_tank} {unit} of {chem['trade_names'][0]} ({chem['active_ingredient']}), mix thoroughly with a wooden paddle, and spray with hollow-cone nozzle."
            })

        plain_summary = (
            f"For your {area_acres} acre plot, prepare {total_tanks} knapsack tanks (capacity {tank_capacity_liters}L each). "
            f"Mix {chem_per_tank} {unit} of {chem['trade_names'][0]} per tank in {tank_capacity_liters}L of water. "
            f"Total chemical needed: {total_chemical_needed} {unit}. "
            f"Observe a Pre-Harvest Interval (PHI) of {chem['phi_days']} days before harvesting."
        )

        return {
            "chemical_id": chemical_id,
            "chemical_name": chem["active_ingredient"],
            "trade_names": chem["trade_names"],
            "area_acres": area_acres,
            "tank_capacity_liters": tank_capacity_liters,
            "total_water_liters": total_water_liters,
            "total_tanks_required": total_tanks,
            "chemical_per_tank": chem_per_tank,
            "unit": unit,
            "total_chemical_needed": total_chemical_needed,
            "phi_days": chem["phi_days"],
            "rei_hours": chem["rei_hours"],
            "toxicity_color": chem["toxicity_color"],
            "plain_farmer_summary": plain_summary,
            "batch_instructions": batch_instructions,
            "safety_ppe": chem["safety_ppe"],
            "application_guidelines": chem["application_notes"]
        }

    @staticmethod
    def get_all_chemicals() -> List[Dict[str, Any]]:
        return list(CIBRC_CHEMICAL_DATABASE.values())
