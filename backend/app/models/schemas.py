from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel


# --- Address ---

class AddressRequest(BaseModel):
    address: str


class AddressCandidate(BaseModel):
    formatted_address: str
    lat: float
    lng: float
    place_id: Optional[str] = None


class AddressResponse(BaseModel):
    candidates: List[AddressCandidate]
    needs_confirmation: bool


class ConfirmAddressRequest(BaseModel):
    lat: float
    lng: float
    formatted_address: str


# --- Parcel ---

class ParcelSummary(BaseModel):
    apn: str
    address: str
    lot_size_sqft: Optional[float] = None
    geometry: Optional[dict] = None  # GeoJSON


class BuildingFootprint(BaseModel):
    building_type: Optional[str] = None
    sqft: Optional[float] = None
    geometry: Optional[dict] = None


class ZoningInfo(BaseModel):
    base_zone: Optional[str] = None
    height_district: Optional[str] = None
    hillside: bool = False
    coastal_zone: bool = False
    fire_hazard: Optional[str] = None
    hpoz: bool = False
    specific_plan: Optional[str] = None
    flood_zone: Optional[str] = None


class ParcelResponse(BaseModel):
    parcel: ParcelSummary
    buildings: List[BuildingFootprint]
    zoning: ZoningInfo


# --- Assessment ---

class AssessRequest(BaseModel):
    apn: str
    building_type: str  # SFH, ADU, GuestHouse


class Constraint(BaseModel):
    rule: str
    value: str
    applied_to_parcel: str
    citation: str
    confidence: str  # HIGH, MEDIUM, LOW
    type: str  # deterministic, interpretive


class ConfidenceBreakdown(BaseModel):
    data_quality: float  # 0.0 - 1.0
    rule_confidence: float  # 0.0 - 1.0
    overall: float  # data_quality * rule_confidence
    grade: str  # A/B/C/D
    factors: List[str]  # human-readable explanations


class AssessmentResponse(BaseModel):
    apn: str
    building_type: str
    buildable: Optional[bool] = None
    confidence_score: float
    confidence_grade: str
    confidence_breakdown: Optional[ConfidenceBreakdown] = None
    summary: str
    constraints: List[Constraint]
    open_questions: List[str]


# --- Chat ---

class ChatRequest(BaseModel):
    apn: str
    message: str


class ChatResponse(BaseModel):
    reply: str


# --- Pipeline progress ---

class PipelineStep(BaseModel):
    step: str
    status: str  # pending, in_progress, complete, error
    detail: Optional[str] = None
