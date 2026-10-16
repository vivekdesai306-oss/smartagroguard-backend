"""
Pydantic Schemas for Knapsack Tank Dilution & Chemical Dosage Calculations
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TankCalculationRequest(BaseModel):
    chemical_id: str = Field(..., description="CIBRC chemical identifier")
    area_acres: float = Field(default=1.0, ge=0.1, le=500.0, description="Field size in acres")
    tank_capacity_liters: float = Field(default=15.0, ge=5.0, le=50.0, description="Knapsack sprayer tank capacity (15L or 20L)")
    water_volume_per_acre_liters: float = Field(default=200.0, ge=50.0, le=500.0, description="Total spray volume needed per acre")

class TankBatchStep(BaseModel):
    tank_number: int
    water_liters: float
    chemical_amount: float
    unit: str
    action_instruction: str

class TankCalculationResponse(BaseModel):
    chemical_id: str
    chemical_name: str
    trade_names: List[str]
    area_acres: float
    tank_capacity_liters: float
    total_water_liters: float
    total_tanks_required: int
    chemical_per_tank: float
    unit: str
    total_chemical_needed: float
    phi_days: int
    rei_hours: int
    toxicity_color: str
    plain_farmer_summary: str
    batch_instructions: List[TankBatchStep]
    safety_ppe: List[str]
    application_guidelines: str
