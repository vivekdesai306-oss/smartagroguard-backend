"""
FAO-56 Penman-Monteith Evapotranspiration & Smart Irrigation Engine
Calculates:
1. Reference Evapotranspiration (ET0) via FAO-56 radiation/temperature/wind/humidity model.
2. Dynamic Maize Crop Water Demand: ETc = Kc * ET0.
3. Root-zone soil moisture depletion & management allowed depletion (MAD).
4. Exact water volume needed (Liters/Acre & mm) and drip pump run-time hours.
5. Crop stunting root-cause triage (Moisture deficit vs Nutrient deficiency).
"""
import math
from typing import Dict, Any, Optional
from ..data.fao56_crop_coefficients import MAIZE_FAO56_KC_STAGES, INDIAN_SOIL_HYDRAULICS

class IrrigationService:
    @staticmethod
    def get_kc_for_das(das: int) -> Dict[str, Any]:
        """
        Retrieves the exact FAO-56 Kc crop coefficient based on Days After Sowing (DAS).
        """
        if das <= 15:
            return MAIZE_FAO56_KC_STAGES["INITIAL"]
        elif das <= 42:
            # Linear interpolation between initial (0.40) and mid (1.15)
            frac = (das - 15) / (42 - 15)
            kc = round(0.40 + frac * (1.15 - 0.40), 2)
            stage_data = MAIZE_FAO56_KC_STAGES["DEVELOPMENT"].copy()
            stage_data["kc_value"] = kc
            return stage_data
        elif das <= 75:
            return MAIZE_FAO56_KC_STAGES["MID_SEASON"]
        elif das <= 100:
            # Linear decline from 1.15 to 0.75
            frac = (das - 75) / (100 - 75)
            kc = round(1.15 - frac * (1.15 - 0.75), 2)
            stage_data = MAIZE_FAO56_KC_STAGES["LATE_SEASON"].copy()
            stage_data["kc_value"] = kc
            return stage_data
        else:
            return MAIZE_FAO56_KC_STAGES["MATURATION"]

    @classmethod
    def calculate_fao56_et0(
        cls,
        temp_c: float = 30.0,
        humidity_pct: int = 65,
        wind_speed_kmh: float = 8.0,
        solar_radiation_mj: float = 18.5
    ) -> float:
        """
        FAO-56 Penman-Monteith Reference Evapotranspiration (ET0 in mm/day).
        ET0 = (0.408*Delta*(Rn - G) + gamma*(900/(T+273))*u2*(es - ea)) / (Delta + gamma*(1 + 0.34*u2))
        """
        # Wind speed at 2m (convert km/h to m/s)
        u2 = max(0.5, wind_speed_kmh / 3.6)
        
        # Saturation vapor pressure (es in kPa)
        es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
        # Actual vapor pressure (ea in kPa)
        ea = es * (humidity_pct / 100.0)
        
        # Slope of vapor pressure curve (Delta in kPa/°C)
        delta = (4098.0 * es) / ((temp_c + 237.3) ** 2)
        
        # Psychrometric constant (gamma in kPa/°C) at ~200m altitude
        gamma = 0.066
        
        # Net radiation equivalent (Rn in mm/day) ~ solar_radiation * 0.408 * 0.77 (albedo 0.23)
        rn_mm = solar_radiation_mj * 0.408 * 0.77
        g_flux = 0.0 # Soil heat flux is negligible on daily scale
        
        numerator = (0.408 * delta * (rn_mm - g_flux)) + (gamma * (900.0 / (temp_c + 273.0)) * u2 * (es - ea))
        denominator = delta + (gamma * (1.0 + 0.34 * u2))
        
        et0 = round(numerator / denominator, 2)
        return max(1.5, min(10.0, et0)) # Sanity clamp for tropical/subtropical India

    @classmethod
    def calculate_irrigation_budget(
        cls,
        area_acres: float = 1.0,
        soil_type: str = "Sandy Loam (Goradu)",
        das: int = 45,
        temperature_c: float = 30.0,
        humidity_percent: int = 65,
        wind_speed_kmh: float = 8.0,
        solar_radiation_mj: float = 18.5,
        rainfall_7d_mm: float = 0.0,
        irrigation_method: str = "Drip",
        drip_flow_rate_lph: float = 4.0,
        simulated_soil_vwc_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive daily water balance and irrigation run-time computation.
        """
        soil_info = INDIAN_SOIL_HYDRAULICS.get(soil_type, INDIAN_SOIL_HYDRAULICS["Sandy Loam (Goradu)"])
        stage_info = cls.get_kc_for_das(das)
        kc = stage_info["kc_value"]

        # 1. Compute ET0 and ETc
        et0 = cls.calculate_fao56_et0(
            temp_c=temperature_c,
            humidity_pct=humidity_percent,
            wind_speed_kmh=wind_speed_kmh,
            solar_radiation_mj=solar_radiation_mj
        )
        etc_mm = round(kc * et0, 2)

        # 2. Water Volume per Acre (1 mm rain/water across 1 acre = 4046.86 Liters)
        water_liters_per_acre = round(etc_mm * 4046.86, 1)
        total_water_volume_liters = round(water_liters_per_acre * area_acres, 1)

        # 3. Soil Moisture Depletion
        fc = soil_info["field_capacity_pct"]
        pwp = soil_info["wilting_point_pct"]
        mad_frac = stage_info["mad_fraction"]

        # If live telemetry sensor available, use it; otherwise compute from weather deficit
        if simulated_soil_vwc_pct is not None:
            current_vwc = round(simulated_soil_vwc_pct, 1)
        else:
            # Weather proxy depletion: 7-day cumulative rainfall vs ETc accumulation
            est_depletion = max(0.0, (etc_mm * 7.0) - (rainfall_7d_mm * 0.8)) # 80% effective rain
            # Convert mm depletion into VWC reduction
            vwc_drop = (est_depletion / (soil_info["total_available_water_mm_per_m"])) * (fc - pwp)
            current_vwc = round(max(pwp, fc - vwc_drop), 1)

        # Moisture deficit threshold (Management Allowed Depletion)
        critical_vwc = round(fc - (mad_frac * (fc - pwp)), 1)

        if current_vwc >= fc:
            deficit_status = "OPTIMAL"
            needs_water = False
        elif current_vwc >= critical_vwc:
            deficit_status = "MODERATE_DEFICIT"
            needs_water = False if das > 100 else True
        elif current_vwc > pwp:
            deficit_status = "CRITICAL_STRESS"
            needs_water = True
        else:
            deficit_status = "CRITICAL_STRESS"
            needs_water = True

        # 4. Pump Runtime Calculation
        if irrigation_method.lower() == "drip":
            # Assume 15,000 drip emitters per acre at 4 LPH
            emitters_per_acre = 15000.0
            system_flow_rate_lph = emitters_per_acre * drip_flow_rate_lph * area_acres
            runtime_hours = round(total_water_volume_liters / max(1000.0, system_flow_rate_lph), 2)
            if not needs_water:
                runtime_hours = 0.0
        else:
            # Furrow / Flood: Pump delivery ~ 25,000 LPH (5 HP tubewell)
            runtime_hours = round(total_water_volume_liters / 25000.0, 2)
            if not needs_water:
                runtime_hours = 0.0

        # 5. Stunting Triage Guidance
        if deficit_status == "CRITICAL_STRESS":
            stunting_triage = (
                "CRITICAL WATER STRESS DETECTED: Soil moisture is below the Management Allowed Depletion threshold. "
                "Any observed crop stunting is primarily induced by drought moisture deficit. "
                "DO NOT apply Urea or Nitrogen fertilizers until soil moisture is fully restored, as dry fertilizer will induce root salt burn."
            )
            action_guidance = f"Operate {irrigation_method} pump for {runtime_hours} hours to supply {total_water_volume_liters} Liters across your {area_acres} acre parcel."
        elif needs_water:
            stunting_triage = (
                "MODERATE WATER CONSUMPTION: Crop is actively transpiring in its "
                f"{stage_info['stage_name']} stage. Scheduled irrigation recommended to sustain vegetative surge."
            )
            action_guidance = f"Apply {total_water_volume_liters} Liters ({runtime_hours} hours {irrigation_method} runtime) within the next 24-48 hours."
        else:
            stunting_triage = (
                "SOIL MOISTURE OPTIMAL: Adequate root-zone water content. "
                "Any height delay observed during scanning is caused by nutrient deficiency (Nitrogen/Zinc) or foliar disease rather than water deficit."
            )
            action_guidance = "No irrigation required today. Soil moisture is optimal."

        return {
            "das": das,
            "growth_stage_code": stage_info["stage_code"],
            "growth_stage_name": stage_info["stage_name"],
            "kc_crop_coefficient": kc,
            "et0_reference_mm_per_day": et0,
            "etc_crop_water_demand_mm_per_day": etc_mm,
            "daily_water_liters_per_acre": water_liters_per_acre,
            "total_water_volume_liters": total_water_volume_liters,
            "soil_status": {
                "soil_type": soil_type,
                "field_capacity_pct": fc,
                "wilting_point_pct": pwp,
                "current_estimated_vwc_pct": current_vwc,
                "management_allowed_depletion_pct": critical_vwc,
                "moisture_deficit_status": deficit_status,
                "is_irrigation_needed": needs_water
            },
            "irrigation_method": irrigation_method,
            "recommended_runtime_hours": runtime_hours,
            "stunting_triage_note": stunting_triage,
            "action_guidance": action_guidance
        }
