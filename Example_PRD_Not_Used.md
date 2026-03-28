*Second PRD as requested during the interview*
# PRD – Home Building Regulatory Engine (Cover Hiring Partner Project)

## 1. Overview

For any residential parcel, Cover needs to quickly answer: **“Given this parcel, what can I confidently build?”**  

This project delivers a small but end‑to‑end **regulatory engine** that turns parcel + zoning information into a structured, explainable buildability assessment, with clear citations, confidence signals, and basic visualization for residential parcels in the City of Los Angeles (proof‑of‑concept scope).  

Timebox: 1 week.

---

## 2. Goals and Non‑Goals

### 2.1 Goals

- Provide a **real‑time, structured buildability assessment** for a residential parcel (address or APN input).
- Identify **applicable zoning and regulatory constraints** and show:
  - Constraint value (e.g., max height, setbacks, lot coverage).
  - **Confidence** per constraint.
  - **Evidence and citations** to the underlying data/rules.
  - Clear distinction between **deterministic** facts and **interpretive/inferred** conclusions.
- Offer **basic visualization** of the parcel and any existing buildings (simplified).
- Demonstrate an **architecture** that can scale to additional LA regions and beyond.
- Use **LLM/AI techniques** for regulatory ingestion or reasoning in a small but illustrative way.

### 2.2 Non‑Goals

- Full coverage of all LA zoning codes or agencies.
- Production‑grade performance, security, or multi‑tenant infrastructure.
- Complex user management or auth.
- Full design system or highly polished UI.

---

## 3. Target Users and Use Cases

### 3.1 Target User

- Architect or engineer who:
  - Understands zoning and regulatory language.
  - Can interpret maps, parcels, and constraints.
  - Wants traceable, explainable outputs more than “magic” answers.

### 3.2 Primary Use Cases

1. **Feasibility Check for a Parcel**
   - User enters address/APN and selects building type (e.g., Single Family, ADU, Guest House).
   - System returns a structured buildability report with constraints and citations.

2. **What‑if Exploration**
   - User toggles project inputs (e.g., bedrooms, bathrooms, building type).
   - System updates constraints and/or highlights which rules are impacted.

3. **Code Validation and Trust Building**
   - User inspects how a specific constraint was derived, including rule text, parcel data, and reasoning steps.
   - User can provide feedback if a constraint appears wrong.

---

## 4. Scope

### 4.1 Functional Scope (Must‑Have)

- Input field for **residential address or APN**.
- Selection of **building type**: at minimum:
  - Single Family Home
  - ADU
  - Guest House
- Real‑time **buildability assessment**:
  - Returns key constraints such as:
    - Max height / stories
    - Lot coverage or FAR
    - Front / side / rear setbacks
    - Max units (if applicable)
- For each constraint:
  - Label as **deterministic** vs **interpretive/inferred**.
  - Provide a **confidence signal** (e.g., 0–1 or Low/Medium/High).
  - Show **citations** back to zoning/parcel sources.
  - Provide a short **explanation** of the reasoning.

- **Basic visualization**:
  - Parcel outline (simplified polygon or rectangle).
  - Optional existing building footprint.
  - Optional “buildable area” after setbacks.

- **Interactable interface**:
  - User can:
    - Enter/search parcel.
    - Select building type.
    - See constraints and citations.
    - Click to expand reasoning per constraint.

- **Architecture diagram**:
  - Simple but actionable diagram showing:
    - Data sources
    - Ingestion layer
    - Reasoning engine
    - API/backend
    - Frontend

### 4.2 Bonus (Nice‑to‑Have)

- Responsive to **project inputs** (e.g., bedrooms, bathrooms, parking).
- Mechanism for **feedback** on bad responses.
- Simple **chat‑like interface** for follow‑up questions on results.
- More **interactive map** (hover/click to see regulations per area).
- Generation of **setback geometry** and buildable envelope.
- Simple **admin view** to inspect/adjust regulatory rules and pipeline.

---

## 5. Product Requirements

### 5.1 User Flows

#### Flow 1: Assess Parcel Buildability (Core Flow)

1. User opens app.
2. User enters address or APN.
3. User selects building type (Single Family, ADU, Guest House).
4. User clicks “Assess.”
5. System:
   - Resolves address/APN to parcel.
   - Retrieves parcel attributes (zone, lot size, shape, etc.).
   - Selects relevant zoning rules.
   - Produces constraints with confidence, type, citations, and explanations.
6. UI displays:
   - Map with parcel (and optional existing building).
   - List/table of constraints grouped by category (height, setbacks, density, etc.).
   - For each constraint:
     - Value and units
     - Confidence
     - Deterministic vs interpretive
     - Expandable explanation

#### Flow 2: Simple What‑If Inputs (Bonus)

1. User performs Flow 1.
2. User adjusts project inputs (e.g., bedrooms, bathrooms).
3. System recomputes subset of constraints (e.g., parking requirement) and updates output.

#### Flow 3: Feedback (Bonus)

1. User views a constraint.
2. User clicks “Thumbs up/down” or selects a reason (e.g., “Rule misapplied”).
3. System logs feedback for later analysis.

---

## 6. UX / UI Requirements

### 6.1 Screens

**1) Main Assessment Screen**

- **Header**:
  - Title: “Parcel Buildability Assessment”
- **Inputs**:
  - Text input: Address or APN.
  - Select: Building type.
  - Optional advanced inputs: bedrooms, bathrooms.
  - “Assess” button.
- **Map Panel**:
  - Displays parcel boundary (rough polygon or rectangle).
  - Optional existing building footprint shape.
  - Optional overlay buildable area (setback‑adjusted shape).
- **Results Panel**:
  - Section: “Summary”
    - Short summary sentence (e.g., “Single Family Home allowed, max 2 stories, approx 2,400 sqft envelope.”)
  - Section: “Constraints”
    - Table or list of constraints:
      - Name (e.g., Max Height)
      - Value (25 ft)
      - Confidence (High/Medium/Low)
      - Type (Deterministic / Interpretive)
      - “Details”/“Why?” link or expand icon.
  - When expanded:
    - Detailed reasoning:
      - Parcel fields used.
      - Rule ID + section.
      - Natural language explanation.

**2) Optional Admin / Rules Screen (Bonus)**

- List of ingested zoning rules.
- Filter by zone, rule type, building type.
- View/edit rule parameters.

### 6.2 UX Principles

- Prioritize **clarity and traceability** over volume of rules.
- Make “deterministic vs interpretive” visually obvious (tags or chips).
- Keep the number of clicks low to reach a buildability summary (1–2 actions).

---

## 7. Technical Requirements

### 7.1 Stack

- Backend: Python (e.g., FastAPI or Flask).
- Frontend: JavaScript/TypeScript (e.g., React).
- Storage:
  - Minimal DB (e.g., Postgres) or in‑memory data with clear path to Postgres/PostGIS.
- Cloud: Design assuming deployment to AWS (or similar), but no need to fully implement hosting.

### 7.2 Data Models (Conceptual)

#### Parcel

- `id`
- `address`
- `apn`
- `zone` (e.g., R1)
- `lot_size_sqft`
- `geometry` (simplified polygon or width/length)
- Optional:
  - `existing_building_footprint` (polygon or dims)

#### RegulatoryRule

- `id`
- `zone` (R1, etc.)
- `building_type` (SFR, ADU, Guest House, or “any”)
- `rule_type` (height, setback_front, setback_side, lot_coverage, etc.)
- `parameters` (JSON; e.g., `{ "max_height_ft": 25 }`)
- `source_section` (e.g., “LAMC §12.XX”)
- `text_snippet` (brief rule text excerpt)
- `is_interpretive` (bool or enum)
- `confidence_default` (e.g., 0.9)

#### ConstraintOutput

- `name`
- `category` (height, setbacks, density, parking)
- `value`
- `units`
- `confidence`
- `type` (deterministic | interpretive)
- `citations` (list of `source_section` / rule IDs / parcel data)
- `explanation` (short natural language string)

### 7.3 APIs

#### `POST /assess`

- **Request body:**
  - `address` or `apn`
  - `building_type`
  - Optional project inputs: `bedrooms`, `bathrooms`, etc.
- **Response:**
  - `parcel`:
    - `id`, `address`, `apn`, `zone`, `lot_size_sqft`, `geometry`
  - `summary`:
    - `text`
  - `constraints`: array of `ConstraintOutput`
  - Optional:
    - `warnings` or `notes`

#### `POST /feedback` (Bonus)

- **Request body:**
  - `parcel_id`
  - `constraint_id` or name
  - `rating` (up/down)
  - Optional: `comment`

---

## 8. AI / LLM Involvement

- At least one part of the system should clearly use **LLM/AI/ML**:
  - Option A: Regulatory ingestion — take raw zoning text snippets and produce structured `RegulatoryRule` records.
  - Option B: Reasoning — given selected rules and parcel data, generate natural language explanations and confidence.
- For the 1‑week scope, LLM use can be:
  - A scripted offline step with sample outputs.
  - Or a small runtime call limited to explanation generation.

---

## 9. Architecture

### 9.1 High‑Level Components

- **Frontend**:
  - Single‑page app calling backend APIs.
  - Map/visualization and constraints display.
- **Backend Service**:
  - Endpoints: `/assess`, optional `/feedback`, optional `/rules`.
  - Contains reasoning engine and integrates with data store.
- **Data Store**:
  - Parcel data.
  - Regulatory rules.
  - Optional feedback logs.
- **Regulatory Ingestion Pipeline**:
  - Script or service that:
    - Takes zoning text.
    - Produces structured `RegulatoryRule` entries.
    - Optionally uses an LLM for tagging and parameter extraction.

### 9.2 Architecture Diagram (Narrative)

The diagram should show:

- Zoning text → Ingestion (LLM) → Rule store.
- Parcel data store.
- Backend reasoning engine combining parcel + rules → constraints.
- API responding to frontend.
- Frontend map + constraints view.

---

## 10. Success Metrics

- Functional coverage:
  - All must‑have requirements demonstrably present.
- UX:
  - Architect/engineer can:
    - Understand main constraints at a glance.
    - Inspect reasoning and citations.
- Technical:
  - End‑to‑end assessment completes in under a few seconds for a test parcel.
  - Architecture and data models clearly support extension to:
    - More zones.
    - More jurisdictions.
    - Richer rules.

---

## 11. Timeline (1 Week)

- **Day 1**: Finalize scope and PRD; design data models and architecture diagram.
- **Day 2**: Implement basic backend models, seed parcels and rules.
- **Day 3**: Implement reasoning engine and `/assess` endpoint.
- **Day 4**: Build frontend: input form, map visualization, constraints table.
- **Day 5**: Add confidence, deterministic/interpretive labels, explanations, and citations.
- **Day 6**: Optional bonuses (project inputs, feedback, simple chat), polish UI and diagram.
- **Day 7**: Testing, cleanup, README, demo script, screenshots.

---

## 12. Risks and Trade‑offs

- Limited time means only a **small subset of rules/zones** will be covered.
- Heavy reliance on **mock data** and simplified geometry.
- LLM use may be illustrative rather than robust.

Documented mitigation: explicit scoping, clear assumptions in README, and an architecture that makes extension straightforward.
