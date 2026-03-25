from pydantic import BaseModel


# --- Address ---

class AddressRequest(BaseModel):
    address: str


class AddressCandidate(BaseModel):
    formatted_address: str
    lat: float
    lng: float
    place_id: str | None = None


class AddressResponse(BaseModel):
    candidates: list[AddressCandidate]
    needs_confirmation: bool


class ConfirmAddressRequest(BaseModel):
    lat: float
    lng: float
    formatted_address: str


# --- Parcel ---

class ParcelSummary(BaseModel):
    apn: str
    address: str
    lot_size_sqft: float | None = None
    geometry: dict | None = None  # GeoJSON


class BuildingFootprint(BaseModel):
    building_type: str | None = None
    sqft: float | None = None
    geometry: dict | None = None


class ZoningInfo(BaseModel):
    base_zone: str | None = None
    height_district: str | None = None
    hillside: bool = False
    coastal_zone: bool = False
    fire_hazard: str | None = None
    hpoz: bool = False
    specific_plan: str | None = None
    flood_zone: str | None = None


class ParcelResponse(BaseModel):
    parcel: ParcelSummary
    buildings: list[BuildingFootprint]
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


class AssessmentResponse(BaseModel):
    apn: str
    building_type: str
    buildable: bool | None = None
    confidence_score: float
    confidence_grade: str
    summary: str
    constraints: list[Constraint]
    open_questions: list[str]


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
    detail: str | None = None
