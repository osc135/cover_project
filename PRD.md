*The PRD I used*
# Home Building Regulatory Engine — PRD

**Cover — Fullstack Hiring Project**
**March 2026 | Version 1.0**

---

## 1. Overview

### 1.1 Problem Statement

One of the key early questions for any residential construction project is: for a given parcel, what can I confidently build? While zoning codes and regulatory documents exist, they are distributed across multiple sources and require expert interpretation to translate general rules into parcel-specific constraints.

The core challenge is producing an evidence-backed buildability assessment that synthesizes these sources into a clear statement of what is allowed, the confidence in that conclusion, and the specific data and rules that support it.

### 1.2 Business Context

At Cover, every project begins with determining what can realistically be built on a site — yet this process is often slow and manual due to fragmented regulatory research. A reliable, evidence-backed buildability assessment would allow Cover to:

- Provide faster and more transparent feasibility guidance
- Help clients make informed decisions earlier
- Reduce entitlement surprises and build trust in the process
- Massively speed up the design team's ability to assess property buildability

### 1.3 Key Impact Metrics

- Reduce regulatory research effort to zero
- Answer buildability questions in real-time as inputs change
- Consistent, cited regulatory answers across all parcels

---

## 2. Scope

### 2.1 Geographic Scope

Proof of concept limited to residential parcels within the City of Los Angeles as a representative test environment.

### 2.2 Building Types Supported

- Single Family Home (SFH)
- Accessory Dwelling Unit (ADU)
- Guest House

### 2.3 Out of Scope (v1)

- Commercial or industrial parcels
- Parcels outside City of Los Angeles jurisdiction
- Full regulatory coverage — a well-reasoned subset of rules is sufficient

---

## 3. Target User

The initial target user is an Architect or Engineer with knowledge of zoning code and regulations. They:

- Can validate the claims made by the tool
- Know how to read a map and understand parcels
- Understand technical regulatory language
- Need to move quickly from site identification to feasibility assessment

---

## 4. Technical Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Vue + TypeScript | Matches Cover's existing stack |
| Mapping | Google Maps JavaScript API | Satellite imagery, polygon rendering, familiar UI for architects; single GCP account covers both mapping and geocoding |
| Backend | Python + FastAPI | Project requirement, async support |
| Database | PostgreSQL + PostGIS + PGVector | Unified DB for spatial and vector data |
| Geocoding | Google Maps Geocoding API + LA City Centerline Locator fallback | GCP-hosted, shared API key with Maps JS; Centerline Locator as LA-specific fallback |
| Parcel Data | LA County ArcGIS REST APIs | Official source, GeoJSON output |
| Zoning Data | LA City GeoHub ArcGIS layers | Point-in-polygon queries per overlay |
| LLM | Claude API (claude-sonnet) | Strong structured output, citation following |
| Embeddings | OpenAI text-embedding-3-small | Fast, cheap, 1536 dimensions |
| Cloud | Railway (current deployment) + GCP (Maps & Geocoding APIs) | Railway for rapid iteration; AWS recommended for production scale |
| Containers | Docker | Matches Cover's infrastructure stack |

---

## 5. Data Sources

### 5.1 GIS / Spatial APIs

All spatial queries use the same ArcGIS REST point-in-polygon pattern — send lat/lng, receive GeoJSON features.

| Source | Data Provided | Endpoint |
|--------|--------------|----------|
| Google Maps Geocoding API | Primary geocoding — address to lat/lng | `maps.googleapis.com/maps/api/geocode` |
| LA City Centerline Locator | Fallback geocoding — LA-specific address resolution | `maps.lacity.org/lahub/rest/services/centerlineLocator` |
| LA County Parcel API | Parcel geometry, APN, lot size | `public.gis.lacounty.gov/.../LACounty_Parcel/MapServer/0` |
| LA City Zoning Layer | Base zone designation (R1, R2, RD, etc.) | `geohub.lacity.org` — Zoning Polygons layer |
| LA City GeoHub | Overlay zones — Hillside, HPOZ, Specific Plans, Coastal | `geohub.lacity.org` — multiple layers |
| LARIAC Buildings 2020 | Existing building footprints on parcel | `public.gis.lacounty.gov/.../LARIAC_Buildings_2020/MapServer/0` |
| FEMA / Fire Hazard layers | Flood zone, fire hazard severity zone | LA City GeoHub |

### 5.2 Regulatory Knowledge Base

The following LAMC sections are downloaded as PDFs, parsed, chunked by subsection, embedded, and stored in PGVector. This pre-processing happens once at setup time — zero latency impact at query time.

| LAMC Section | Content |
|-------------|---------|
| Section 12.03 | Definitions — ADU, Floor Area, Residential Floor Area, etc. |
| Section 12.04 | Zone definitions and full zone type hierarchy |
| Section 12.08 | R1 One-Family Zone — setbacks, height, FAR, lot coverage |
| Section 12.09 | R2 Two-Family Zone rules |
| Section 12.09.1 | RD Restricted Density Zone rules |
| Section 12.21 | Height districts and floor area ratio rules |
| Section 12.22 | Accessory uses including ADU regulations |

---

## 6. Database Schema

### 6.1 Tables Overview

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `parcels` | Core parcel records | `apn`, `address`, `lot_size_sqft`, `geometry` (PostGIS POLYGON) |
| `buildings` | Existing structures on parcel | `apn` (FK), `building_type`, `sqft`, `geometry` (PostGIS POLYGON) |
| `zoning_designations` | All zone overlays per parcel | `apn` (FK), `base_zone`, `height_district`, `hillside`, `coastal_zone`, `fire_hazard`, `hpoz`, `specific_plan`, `flood_zone` |
| `regulatory_chunks` | Pre-processed LAMC text chunks | `section_id`, `zone`, `topic`, `text`, `source_url`, `embedding` (VECTOR 1536) |
| `assessments` | Cached LLM assessment results | `apn` (FK), `building_type`, `buildable`, `confidence_score`, `constraints` (JSONB), `open_questions` (JSONB) |

### 6.2 Key Design Decisions

- PostGIS handles all spatial data — parcel polygons, building footprints, zone boundaries
- PGVector handles all regulatory embeddings — 1536-dimension vectors with IVFFlat index for fast similarity search
- `raw_response` JSONB stored everywhere — preserves original API data for reprocessing without re-hitting APIs
- Assessments cached by APN + building type — same query never hits LLM twice
- Single Postgres instance for both PostGIS and PGVector — no separate vector database needed

---

## 7. API Endpoints

### 7.1 Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/resolve-address` | Geocode address, return candidates for user confirmation |
| `POST` | `/api/confirm-address` | User confirms candidate — triggers full data collection pipeline |
| `GET` | `/api/parcel/{apn}` | Fetch previously looked up parcel by APN |
| `POST` | `/api/assess` | Run or retrieve cached buildability assessment |
| `GET` | `/api/assessment/{apn}/{building_type}` | Fetch cached assessment without re-running LLM |
| `GET` | `/api/health` | Service health check |
| `POST` | `/api/chat` | Chat follow-up questions about an assessment *(bonus)* |
| `POST` | `/api/feedback` | Submit feedback on an incorrect assessment *(bonus)* |

### 7.2 Confirm Address Pipeline

The `/api/confirm-address` endpoint triggers a sequential pipeline after user confirms their address. The frontend shows live progress as each step completes:

1. Address confirmed
2. Fetching parcel data from LA County...
3. Loading zoning designations...
4. Checking overlay zones...
5. Fetching existing building footprints...
6. Retrieving relevant regulations...
7. Generating buildability assessment...
8. Complete

---

## 8. RAG Pipeline

### 8.1 Ingestion (Offline, Run Once)

1. Download target LAMC sections as PDFs from amlegal
2. Parse PDFs using pdfplumber — extract text by page
3. Split text by subsection headers using regex patterns (e.g. `12.08 C.1`)
4. Apply 50–100 token overlap at chunk boundaries to preserve cross-reference context
5. Generate embeddings using OpenAI text-embedding-3-small (1536 dimensions)
6. Store chunks + embeddings in PGVector `regulatory_chunks` table
7. Index with IVFFlat for fast cosine similarity search

### 8.2 Retrieval (At Query Time)

At query time, retrieval combines a hard filter with semantic similarity search:

- Hard filter by zone code (`WHERE zone = 'R1'`) — prevents cross-zone rule contamination
- Semantic similarity search using cosine distance operator (`<=>`)
- Return top 10 most relevant chunks for the query
- Query constructed dynamically from zone code + building type + specific question

### 8.3 Generation

- Retrieved chunks passed to Claude API as context
- Parcel data included alongside regulatory chunks
- Structured JSON output enforced via prompt instructions
- Response parsed and stored in `assessments` table

---

## 9. LLM Assessment Layer

### 9.1 Input Context

Each LLM call receives the following context:

- **Parcel data** — address, APN, lot size, existing buildings, all zone designations
- **Building type** being assessed — SFH, ADU, Guest House
- **Retrieved regulatory chunks** — top 10 most relevant LAMC sections

### 9.2 Structured Output Format

The LLM returns a structured JSON assessment:

- `summary` — one paragraph plain English verdict
- `buildable` — boolean top-level determination
- `confidence_score` — 0.0 to 1.0 derived from individual constraint confidence levels
- `confidence_grade` — A/B/C/D letter grade for quick human readability
- `constraints` — array of individual rule assessments, each containing:
  - `rule` — name of the constraint
  - `value` — the raw regulatory limit
  - `applied_to_parcel` — how the rule applies to this specific lot
  - `citation` — exact LAMC section number
  - `confidence` — HIGH / MEDIUM / LOW
  - `type` — deterministic or interpretive
- `open_questions` — array of flagged uncertainties requiring human verification

### 9.3 Confidence Scoring

Overall confidence score is derived from individual constraint confidence levels:

| Grade | Score | Meaning |
|-------|-------|---------|
| A | 90%+ | All constraints HIGH — rules directly stated, parcel data complete |
| B | 75–89% | Mix of HIGH and MEDIUM — mostly clear with minor interpretive steps |
| C | 60–74% | Several LOW confidence or interpretive constraints |
| D | <60% | Many ambiguous rules or missing data — flag for professional review |

### 9.4 Confidence Drivers

**Confidence decreases when:**
- Overlay zones found that are not in the regulatory knowledge base
- Rule text contains conditional logic referencing sections not ingested
- Parcel data fields are incomplete or estimated
- Specific Plan or Coastal Zone applies — these have complex separate rule sets

**Confidence increases when:**
- Rule directly and unambiguously stated in code
- Parcel data cleanly retrieved from GIS with no gaps
- No conflicting rules found across layers

---

## 10. Frontend Design

### 10.1 User Flow

The user experience is intentionally simple — three visible steps:

1. Type an address or APN into the search input
2. Confirm the address from returned candidates (if ambiguous)
3. View the full buildability assessment with parcel map

### 10.2 UI Sections

| Section | Content |
|---------|---------|
| Address Input | Text input with autocomplete, candidate confirmation modal if score < 95 or multiple results |
| Progress Indicator | Live step-by-step status as backend pipeline executes — shows what the system is doing |
| Parcel Header | APN, address, lot size, zone designation — deterministic facts from GIS |
| Map (Google Maps) | Parcel boundary polygon, existing building footprints, satellite imagery, setback overlays *(bonus)* |
| Zone Designations | All applicable zones with coverage status — rules available vs. not indexed vs. flagged |
| Buildability Summary | Overall verdict, confidence grade badge, one-paragraph plain English summary |
| Constraints Table | Each rule with citation, parcel application, confidence level — color coded |
| Open Questions | Flagged uncertainties the system could not resolve — prompts for professional review |
| Building Type Selector | Switch between SFH / ADU / Guest House — re-runs assessment for selected type |
| Chat Interface *(bonus)* | Follow-up Q&A about the assessment grounded in retrieved regulatory context |

### 10.3 Zone Coverage Display

Each zone designation found on the parcel shows its coverage status:

- **✓ Rules available** — fully assessed, high confidence
- **⚠ Rules not fully indexed** — partially assessed, confidence reduced
- **— Not applicable** — zone does not apply to this parcel
- **! Consult specialist** — zone requires domain expertise beyond current scope

---

## 11. Functional Requirements

### 11.1 Must-Haves

- Address or APN input with geocoding and candidate confirmation
- Full parcel data retrieval from LA County and City GIS APIs
- All applicable zone designations identified and displayed
- Structured buildability assessment with cited LAMC sections
- Confidence score and grade at both constraint and overall level
- Clear distinction between deterministic facts and interpretive conclusions
- Parcel boundary and existing building visualization on Google Maps
- Support for SFH, ADU, and Guest House building types
- Live progress indicator during pipeline execution
- Architecture diagram for productionization

### 11.2 Bonus Features

- Chat interface for follow-up questions about the assessment
- User feedback mechanism for flagging incorrect responses
- Interactive map with setback geometry overlaid on parcel
- Project-specific inputs (bedrooms, bathrooms) influencing assessment
- Admin interface for regulatory engine pipeline management

---

## 12. Production Architecture

### 12.1 Component Overview

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| Frontend | Vue + TypeScript + Google Maps | User interface, address input, map, assessment display |
| API Gateway | FastAPI | Request routing, validation, orchestration |
| Geocoding Service | Google Maps Geocoding API + LA Centerline Locator fallback | Address to lat/lng resolution |
| GIS Service | ArcGIS REST APIs (LA County + City) | Parcel, zoning, buildings data collection |
| RAG Service | PGVector + OpenAI Embeddings | Regulatory chunk retrieval by zone and query |
| LLM Service | Claude API | Buildability assessment generation |
| Database | PostgreSQL + PostGIS + PGVector | All persistent data storage |
| Cache Layer | Assessment table in Postgres | Avoid re-running LLM for identical queries |
| Ingestion Script | Python + pdfplumber | One-time offline regulatory PDF processing |
| Infrastructure | Railway (current), AWS recommended for production | Hosting and deployment |

### 12.2 Scalability Considerations

- Zone filter before vector search prevents cross-jurisdiction rule contamination as coverage expands
- Ingestion script is re-runnable — adding new jurisdictions means adding new PDFs and re-ingesting
- Assessment caching means popular parcels return instantly without LLM calls
- PostGIS spatial indexing supports scaling to all of LA County, then broader California
- Modular GIS service layer allows swapping data sources per jurisdiction without touching LLM layer

---

## 13. Development Timeline

| Day | Focus | Deliverables |
|-----|-------|-------------|
| 1–2 | Foundation | Postgres setup (PostGIS + PGVector), FastAPI project structure, PDF ingestion script, regulatory chunks in DB |
| 2–3 | Data Layer | Geocoding endpoint, parcel lookup, all zoning overlay queries, buildings lookup, all GIS endpoints working |
| 3–4 | LLM Layer | RAG retrieval query, prompt template, Claude API integration, structured JSON parsing, assessment caching |
| 4–5 | Frontend | Vue project setup, address input + confirmation flow, Google Maps parcel visualization, assessment output UI |
| 5–6 | Polish | Error handling, confidence scoring, progress indicators, testing across multiple addresses and building types |
| 7 | Buffer + Docs | Architecture diagram, README, cleanup, bonus features if time allows |

---

## 14. Open Questions & Risks

| Question / Risk | Impact | Mitigation |
|----------------|--------|------------|
| amlegal PDF download restrictions | High — blocks regulatory ingestion | Target specific section URLs, use PDF download directly, mock data as fallback |
| Google Maps API key required | Low — straightforward GCP setup | Single GCP project with Maps JavaScript API + Geocoding API enabled; LA Centerline Locator as free fallback |
| Parcel zoning layer missing base zone field | High — zone lookup fails | Query separate City zoning layer, test early |
| Hillside / Specific Plan rules not ingested | Medium — confidence drops for affected parcels | Flag explicitly in open questions, document as known gap |
| LLM hallucinating LAMC citations | High — trust broken with architects/engineers | Validate citations against stored chunks, flag unverifiable citations |
| GIS API rate limits | Low — POC volume is low | Cache all parcel data after first lookup |
