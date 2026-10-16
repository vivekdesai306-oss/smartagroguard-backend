from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    user_name: str = Field(..., min_length=3, max_length=30)
    user_role: str = Field("Farmer", description="Farmer / Agronomy Admin / System Admin")
    password: str = Field(..., min_length=6)
    email: EmailStr
    mobile_no: str = Field(..., min_length=10, max_length=15)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    uid: str
    user_name: str
    user_role: str
    email: EmailStr
    mobile_no: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    uid: Optional[str] = None
    role: Optional[str] = None


# --- Farm Profile Schemas ---
class FarmCreate(BaseModel):
    farm_address: str
    farm_area: Optional[str] = None
    active_crop: Optional[str] = "Corn"
    state: Optional[str] = "Gujarat"
    district: Optional[str] = "Panchmahal"
    taluka: Optional[str] = "Godhra"
    village: Optional[str] = "Vavdi"
    entered_latitude: Optional[float] = 22.7758
    entered_longitude: Optional[float] = 73.6149
    soil_type: Optional[str] = "Sandy Loam (Goradu)"
    season: Optional[str] = "KHARIF"
    sowing_date: Optional[str] = None
    variety: Optional[str] = "GAYMH-1"

class FarmOut(BaseModel):
    farm_id: str
    uid: str
    farm_address: str
    farm_area: Optional[str] = None
    active_crop: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    taluka: Optional[str] = None
    village: Optional[str] = None
    entered_latitude: Optional[float] = None
    entered_longitude: Optional[float] = None
    soil_type: Optional[str] = None
    season: Optional[str] = None
    sowing_date: Optional[str] = None
    variety: Optional[str] = None

    class Config:
        from_attributes = True


# --- Location Verification & Suitability Schemas ---
class LocationVerifyRequest(BaseModel):
    entered_latitude: float
    entered_longitude: float
    gps_latitude: float
    gps_longitude: float
    threshold_meters: Optional[float] = 1000.0

class LocationVerifyResponse(BaseModel):
    status: str  # VERIFIED / MISMATCH / UNVERIFIED
    distance_meters: Optional[float] = None
    threshold_meters: float
    entered_coordinates: Optional[dict] = None
    gps_coordinates: Optional[dict] = None
    headline: str
    message: str
    actions: Optional[List[str]] = None
    timestamp: str

class SuitabilityEvaluateRequest(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    taluka: Optional[str] = None
    village: Optional[str] = None
    entered_latitude: Optional[float] = None
    entered_longitude: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    season: Optional[str] = "KHARIF"
    sowing_date: Optional[str] = None

class SuitabilityReportOut(BaseModel):
    gps_verification: dict
    crop: str = "MAIZE"
    area_suitability: dict
    season_suitability: dict
    sowing_period: dict
    decision: dict


# --- Decoupled Multimodal Architecture Schemas ---

class CropValidationOut(BaseModel):
    validation_stage: str  # CORN / NOT_CORN / NOT_A_CROP
    detected_crop_type: Optional[str] = None
    is_crop: bool
    is_corn: bool
    crop_confidence: float
    headline: str
    explanation: str
    foliage_ratio: Optional[float] = None

class GrowthAssessmentOut(BaseModel):
    visual_week: Optional[str] = None
    visual_confidence: Optional[float] = None
    das: int
    expected_week: Optional[str] = None
    phenological_stage: Optional[str] = None
    biological_phase: Optional[str] = None

class HeightAssessmentOut(BaseModel):
    measured_height_cm: Optional[float] = None
    expected_range_cm: Optional[Dict[str, float]] = None
    expected_range_str: Optional[str] = None
    height_status: str  # WITHIN_EXPECTED / BELOW_EXPECTED / ABOVE_EXPECTED / REJECTED / NO_MARKER
    measurement_source: str  # ARUCO_CALIBRATED / COLOR_MARKER_CALIBRATED / SIMULATED_BENCHMARK / REJECTED
    height_adjustment: Optional[Dict[str, Any]] = None

class EnvironmentContextOut(BaseModel):
    temperature_c: Optional[float] = None
    humidity_percent: Optional[int] = None
    rainfall_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    solar_radiation: Optional[str] = None
    frost_risk: Optional[str] = None
    weather_condition: Optional[str] = None
    soil_type: Optional[str] = None
    season: Optional[str] = None
    source: Optional[str] = None

class HealthInterpretationOut(BaseModel):
    growth_status: str  # NORMAL / STUNTED / OVERGROWN / REJECTED
    is_healthy: bool
    health_headline: str
    contributing_factors: List[str] = []
    disease_diagnosis: Optional[Dict[str, Any]] = None

# --- Legacy Sub-Log Schemas for Backward Compatibility ---
class GrowthStageLogOut(BaseModel):
    stage_log_id: str
    scan_id: str
    detected_stage: str
    confidence_score: Optional[float] = None
    measured_height_cm: Optional[float] = None
    expected_height_range: Optional[str] = None
    height_status: str
    crop_match: bool
    validation_stage: Optional[str] = "CORN"
    species_info: Optional[dict] = None
    recommended_modules: Optional[str] = None
    scan_summary: Optional[str] = None
    height_source: Optional[str] = None

class DiseaseDetectionLogOut(BaseModel):
    disease_log_id: str
    scan_id: str
    detected_disease: Optional[str] = None
    confidence_score: Optional[float] = None
    review_status: str
    engine: Optional[str] = None
    evidence: Optional[dict] = None


# --- Master Crop Scan Schema ---
class ScanOut(BaseModel):
    scan_id: str
    farm_id: str
    crop_type: str
    day_count: int  # DAS
    sowing_date: Optional[str] = None
    image_url: str
    scan_date: datetime
    
    # 3-Layer Decoupled Architecture
    crop_validation: Optional[CropValidationOut] = None
    growth: Optional[GrowthAssessmentOut] = None
    height: Optional[HeightAssessmentOut] = None
    environment: Optional[EnvironmentContextOut] = None
    health: Optional[HealthInterpretationOut] = None
    advisory: List[str] = []
    module3_advisory: Optional[Dict[str, Any]] = None
    
    # Compatibility attributes
    suitability_report: Optional[SuitabilityReportOut] = None
    growth_log: Optional[GrowthStageLogOut] = None
    disease_log: Optional[DiseaseDetectionLogOut] = None
    dosage_details: Optional[str] = None
    agronomic_advisory: Optional[str] = None
    validation_stage: Optional[str] = "CORN"
    species_info: Optional[dict] = None

    class Config:
        from_attributes = True


# =========================================================================
# --- Module 3: Evidence-Based Advisory & Treatment Engine Schemas ---
# =========================================================================
from enum import Enum

class PriorityTierEnum(str, Enum):
    PROTECTION = "PROTECTION"
    CORRECTIVE = "CORRECTIVE"
    MAINTENANCE = "MAINTENANCE"

class StressHypothesisEnum(str, Enum):
    WATER_STRESS = "Water_Stress_Suspected"
    NUTRIENT_DEFICIENCY = "Nutrient_Deficiency_Suspected"
    DISEASE_STRESS = "Disease_Stress_Suspected"
    ENVIRONMENTAL_STRESS = "Environmental_Stress_Suspected"
    INSUFFICIENT_EVIDENCE = "Insufficient_Evidence"
    HEALTHY_OPTIMAL = "Healthy_Optimal"

class RecommendationStatusEnum(str, Enum):
    NO_CHEMICAL_TREATMENT = "NO_CHEMICAL_TREATMENT"
    RESTORE_WATER_AVAILABILITY = "RESTORE_WATER_AVAILABILITY"
    MONITOR_FOR_48_HOURS = "MONITOR_FOR_48_HOURS"
    PERFORM_FIELD_INSPECTION = "PERFORM_FIELD_INSPECTION"
    FERTILIZER_RECOMMENDATION = "FERTILIZER_RECOMMENDATION"
    PESTICIDE_RECOMMENDATION = "PESTICIDE_RECOMMENDATION"
    TREATMENT_NOT_AUTHORIZED = "TREATMENT_NOT_AUTHORIZED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class Module2DiagnosticSignals(BaseModel):
    scan_id: str = Field(..., description="Unique scan identifier")
    visual_week: str = Field("Week 5", description="MobileNetV2 visual growth week (Week 1..11)")
    visual_confidence: float = Field(0.85, ge=0.0, le=1.0, description="Confidence of visual week classifier")
    calculated_das: int = Field(..., ge=0, le=150, description="Calendar Days After Sowing")
    measured_height_cm: Optional[float] = Field(None, ge=0.0, le=350.0, description="OpenCV calibrated height")
    expected_height_range_str: str = Field("50–80 cm", description="Benchmark height range e.g. '50–80 cm'")
    height_status: str = Field("WITHIN_EXPECTED", description="WITHIN_EXPECTED / BELOW_EXPECTED / ABOVE_EXPECTED / NO_MARKER")
    detected_disease: str = Field("Healthy", description="Pathology classification label")
    disease_confidence: float = Field(0.95, ge=0.0, le=1.0, description="Pathology classification confidence")
    review_status: str = Field("Auto-confirmed", description="Auto-confirmed / Pending Admin Review")
    scouting_observations: List[str] = Field(default=[], description="Observed symptoms e.g. ['lower_leaf_chlorosis']")

class EnvironmentalContext(BaseModel):
    rainfall_mm: float = Field(0.0, ge=0.0, description="7-day accumulated rainfall")
    temperature_c: float = Field(28.0, description="Mean temperature in °C")
    humidity_percent: int = Field(65, ge=0, le=100, description="Relative humidity percentage")
    wind_speed_kmh: float = Field(8.0, ge=0.0, description="Current wind speed in km/h")
    hours_until_rain: float = Field(24.0, ge=0.0, description="Hours until forecast rainfall")
    forecast_rain_volume_mm: float = Field(0.0, ge=0.0, description="Forecast rain volume in next 24h")
    season: str = Field("KHARIF", description="Cultivation season")
    district: str = Field("Panchmahal", description="Farm district")
    agro_climatic_zone: str = Field("Middle Gujarat Agro-Climatic Zone III", description="Agro-climatic classification zone")

class FarmGroundTruth(BaseModel):
    farm_id: str = Field(..., description="Unique farm identifier")
    uid: str = Field(..., description="Registered farmer UID")
    crop_type: str = Field("Corn", description="Cultivated crop species")
    variety: str = Field("GAYMH-1", description="Hybrid cultivar variety")
    soil_type: str = Field("Sandy Loam (Goradu)", description="Soil classification")
    farm_area_acres: float = Field(1.0, gt=0.0, le=500.0, description="Total plot area in acres")
    sowing_date: str = Field("2026-06-01", description="Sowing date (YYYY-MM-DD)")

class Module3InputContract(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    diagnostics: Module2DiagnosticSignals
    environment: EnvironmentalContext
    farm: FarmGroundTruth

class DiagnosticAssessment(BaseModel):
    height_status: str
    growth_stage: Optional[int] = None
    growth_stage_confidence: Optional[float] = None
    measured_height_cm: Optional[float] = None
    expected_range_cm: Optional[str] = None
    disease_status: Optional[str] = None
    disease_confidence: Optional[float] = None
    recent_rainfall_mm: Optional[float] = None
    soil_type: Optional[str] = None
    stress_hypothesis: Optional[str] = None
    evidence_summary: List[str] = []
    diagnostic_confidence: Optional[float] = None
    verification_status: str = "NOT_APPLICABLE"

class ScaledTreatmentPlan(BaseModel):
    category: str  # FERTILIZER / PESTICIDE / FUNGICIDE / HERBICIDE
    product_name: str
    active_ingredient: Optional[str] = None
    formulation: Optional[str] = None
    unit_rate: str
    farm_area_acres: float
    total_quantity: str
    water_dilution: Optional[str] = None
    application_method: str
    timing: str
    rainfastness_hours: Optional[float] = None
    safety_notes: Optional[str] = None
    is_conditional: bool = False
    verification_prerequisite: Optional[str] = None

class NonChemicalAction(BaseModel):
    action_type: str  # RESTORE_WATER_AVAILABILITY / MONITOR_FOR_48_HOURS / PERFORM_FIELD_INSPECTION / NO_CHEMICAL_TREATMENT
    headline: str
    instructions: str
    target_module: Optional[str] = None

class Module3Output(BaseModel):
    scan_id: str
    farm_id: str
    timestamp: datetime
    priority_tier: PriorityTierEnum
    recommendation_status: RecommendationStatusEnum
    diagnostic: DiagnosticAssessment
    pesticide_treatment: Optional[ScaledTreatmentPlan] = None
    fertilizer_advisory: Optional[ScaledTreatmentPlan] = None
    non_chemical_action: Optional[NonChemicalAction] = None
    safety_validation: Dict[str, Any]
    farmer_summary: str


# =========================================================================
# --- Module 4: Farm History, Temporal Analytics & Lifecycle Schemas ---
# =========================================================================

# --- Data Quality ---
class DataQualityOut(BaseModel):
    total_scans: int
    valid_height_scans: int
    valid_disease_scans: int
    missing_sowing_date: bool
    das_available: bool
    last_scan_date: Optional[str] = None
    days_since_last_scan: Optional[int] = None
    average_days_between_scans: Optional[float] = None
    longest_gap_days: Optional[int] = None
    quality_level: str  # GOOD / LIMITED / INSUFFICIENT

# --- Response Envelope ---
class Module4ResponseEnvelope(BaseModel):
    farm_id: str
    generated_at: str
    data_quality: DataQualityOut

# --- Timeline ---
class TimelineEntryOut(BaseModel):
    scan_id: str
    scan_date: datetime
    day_count: Optional[int] = None
    growth_week: Optional[str] = None
    measured_height_cm: Optional[float] = None
    height_status: Optional[str] = None
    disease_status: Optional[str] = None
    disease_confidence: Optional[float] = None
    health_composite: Optional[str] = None
    recommendation_status: Optional[str] = None
    image_url: Optional[str] = None

class TimelineResponse(Module4ResponseEnvelope):
    total_count: int
    page: int
    page_size: int
    items: List[TimelineEntryOut]

# --- Growth Curve ---
class GrowthCurvePointOut(BaseModel):
    das: Optional[int] = None
    scan_date: str
    measured_height_cm: Optional[float] = None
    expected_min_cm: Optional[float] = None
    expected_max_cm: Optional[float] = None
    height_status: Optional[str] = None
    growth_week: Optional[str] = None

class GrowthCurveResponse(Module4ResponseEnvelope):
    das_available: bool
    sowing_date: Optional[str] = None
    points: List[GrowthCurvePointOut]
    growth_score_percent: Optional[float] = None
    growth_score_available: bool
    valid_height_scans: int
    within_expected_scans: int

# --- Health Trend ---
class HealthTrendPointOut(BaseModel):
    scan_date: str
    das: Optional[int] = None
    health_status: str
    disease: Optional[str] = None
    disease_confidence: Optional[float] = None

class HealthTrendResponse(Module4ResponseEnvelope):
    points: List[HealthTrendPointOut]

# --- Advisory History ---
class AdvisoryHistoryEntryOut(BaseModel):
    scan_id: str
    scan_date: str
    das: Optional[int] = None
    priority_tier: Optional[str] = None
    recommendation_status: Optional[str] = None
    stress_hypothesis: Optional[str] = None
    farmer_summary: Optional[str] = None
    has_chemical_treatment: bool = False
    has_non_chemical_action: bool = False

class AdvisoryHistoryResponse(Module4ResponseEnvelope):
    items: List[AdvisoryHistoryEntryOut]
    total_advisories: int

# --- Temporal Observations ---
class TemporalObservationOut(BaseModel):
    observation_id: str
    observation_type: str  # HEIGHT_DECREASE_OBSERVED / DISEASE_PERSISTENCE_OBSERVED / RECOVERY_OBSERVED
    severity: str          # INFO / WARNING
    headline: str
    detail: str
    affected_scans: List[str]

class ObservationsResponse(Module4ResponseEnvelope):
    observations: List[TemporalObservationOut]

# --- Season Overview ---
class SeasonOverviewResponse(Module4ResponseEnvelope):
    crop_type: str
    sowing_date: Optional[str] = None
    das_available: bool
    current_das: Optional[int] = None
    total_scans: int
    latest_growth_week: Optional[str] = None
    latest_height_cm: Optional[float] = None
    latest_height_status: Optional[str] = None
    latest_health_status: Optional[str] = None

# --- Season Statistics ---
class SeasonStatisticsResponse(Module4ResponseEnvelope):
    crop_type: str
    sowing_date: Optional[str] = None
    total_scans: int
    lifecycle_days: Optional[int] = None
    growth_score_percent: Optional[float] = None
    growth_score_available: bool
    valid_height_scans: int
    within_expected_scans: int
    latest_growth_status: Optional[str] = None
    latest_health_status: Optional[str] = None
    disease_incidents: int
    unique_diseases: List[str]
    total_advisories: int
    chemical_advisories: int
    non_chemical_advisories: int
    average_days_between_scans: Optional[float] = None
    longest_gap_days: Optional[int] = None


# Module 4 Weather Contracts
from .weather import *

