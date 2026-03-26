export interface AddressCandidate {
  formatted_address: string
  lat: number
  lng: number
  place_id?: string
}

export interface ExistingProperty {
  use_type: string | null
  use_description: string | null
  year_built: number | null
  sqft: number | null
  bedrooms: number | null
  bathrooms: number | null
  land_value: number | null
  improvement_value: number | null
}

export interface ParcelSummary {
  apn: string
  address: string
  lot_size_sqft: number | null
  geometry: GeoJSON.Geometry | null
  existing_property?: ExistingProperty
}

export interface BuildingFootprint {
  building_type: string | null
  sqft: number | null
  geometry: GeoJSON.Geometry | null
}

export interface ZoningInfo {
  base_zone: string | null
  height_district: string | null
  hillside: boolean
  coastal_zone: boolean
  fire_hazard: string | null
  hpoz: boolean
  specific_plan: string | null
  flood_zone: string | null
}

export interface ParcelData {
  parcel: ParcelSummary
  buildings: BuildingFootprint[]
  zoning: ZoningInfo
}

export interface Constraint {
  rule: string
  value: string
  applied_to_parcel: string
  citation: string
  confidence: 'HIGH' | 'MEDIUM' | 'LOW'
  type: 'deterministic' | 'interpretive'
}

export interface ConfidenceBreakdown {
  data_quality: number
  rule_confidence: number
  overall: number
  grade: string
  factors: string[]
}

export interface Assessment {
  apn: string
  building_type: string
  buildable: boolean | null
  confidence_score: number
  confidence_grade: string
  confidence_breakdown?: ConfidenceBreakdown
  summary: string
  constraints: Constraint[]
  open_questions: string[]
}

export interface PipelineStep {
  step: string
  status: 'pending' | 'in_progress' | 'complete' | 'error'
  detail?: string
}
