"""
FastAPI Router for Knapsack Sprayer Tank Dilution & Chemical Dosage Calculations
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from ..schemas.dosage import TankCalculationRequest, TankCalculationResponse
from ..services.dilution_calculator_service import DilutionCalculatorService

router = APIRouter(prefix="/api/v1/dosage", tags=["Precision Chemical & Pesticide Dosage"])

@router.post("/calculate", response_model=TankCalculationResponse)
def calculate_dosage(req: TankCalculationRequest):
    """
    Computes exact chemical batching, knapsack tank requirements, water volumes, and PHI guidelines.
    """
    return DilutionCalculatorService.calculate_knapsack_dilution(
        chemical_id=req.chemical_id,
        area_acres=req.area_acres,
        tank_capacity_liters=req.tank_capacity_liters,
        water_volume_per_acre_liters=req.water_volume_per_acre_liters
    )

@router.get("/chemicals")
def list_chemicals():
    """
    Lists all CIBRC registered chemical formulations with rates, dilution rules, and active ingredients.
    """
    return DilutionCalculatorService.get_all_chemicals()
