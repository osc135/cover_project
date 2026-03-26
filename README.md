# Cover Regulatory Engine

A fullstack application that answers the question: **for a given parcel in Los Angeles, what can I confidently build?**

The system takes a residential address, pulls parcel and zoning data from public GIS APIs, retrieves relevant LA Municipal Code regulations via RAG, and uses an LLM to produce a structured, evidence-backed buildability assessment with citations and confidence scores.

## Architecture

```
                                        +---------------------------+
                                        |        Frontend           |
                                        |   Vue + TypeScript        |
                                        |   Google Maps JS API      |
                                        +------------+--------------+
                                                     |
                                                     | HTTP / SSE
                                                     v
+------------------+               +-----------------+------------------+
|                  |   Address     |                                    |
|  Google Maps     +<--------------+         FastAPI Backend            |
|  Geocoding API   +-------------->+                                    |
|                  |   lat/lng     |  +-------------------------------+ |
+------------------+               |  |     Data Collection Pipeline  | |
                                   |  |                               | |
+------------------+               |  |  1. Geocode address           | |
|  LA County       |   lat/lng     |  |  2. Fetch parcel geometry     | |
|  Parcel API      +<------------->+  |  3. Fetch zoning designation  | |
|  (ArcGIS REST)   |   GeoJSON    |  |  4. Check overlay zones       | |
+------------------+               |  |  5. Fetch building footprints | |
                                   |  |  6. Store in Postgres         | |
+------------------+               |  +-------------------------------+ |
|  LA City GeoHub  |   lat/lng     |                                    |
|  Zoning + Overlay+<------------->+  +-------------------------------+ |
|  (ArcGIS REST)   |   features   |  |     Assessment Pipeline       | |
+------------------+               |  |                               | |
                                   |  |  1. RAG retrieval (PGVector)  | |
+------------------+               |  |  2. Claude LLM assessment    | |
|  LARIAC Buildings|   lat/lng     |  |  3. Cache result in Postgres  | |
|  2020            +<------------->+  |                               | |
|  (ArcGIS REST)   |   footprints |  +-------------------------------+ |
+------------------+               |                                    |
                                   |  +-------------------------------+ |
                                   |  |     Chat (Bonus)              | |
                                   |  |     GPT-4o follow-up Q&A     | |
                                   |  +-------------------------------+ |
                                   +---+-------------------+----------+
                                       |                   |
                                       v                   v
                              +--------+-------+   +------+--------+
                              |   PostgreSQL   |   | Claude API    |
                              |                |   | (Anthropic)   |
                              | - PostGIS-like |   +---------------+
                              |   JSONB geom   |
                              | - PGVector     |   +---------------+
                              |   embeddings   |   | OpenAI API    |
                              | - Parcel data  |   | - Embeddings  |
                              | - Assessments  |   | - GPT-4o Chat |
                              |   (cached)     |   +---------------+
                              +----------------+
```

## How It Works

### 1. Address Resolution
User enters an address. Google Maps Geocoding API resolves it to lat/lng. If the key isn't available, the LA City Centerline Locator is used as a fallback.

### 2. Data Collection Pipeline
Using the lat/lng, the backend queries multiple public ArcGIS REST APIs in sequence:
- **LA County Parcel API** — parcel boundary polygon, APN, lot size, existing building info
- **LA City Zoning Layer** — base zone designation (R1, R2, R3, etc.)
- **Overlay Zone Layers** — HPOZ, Specific Plans, Flood, Fire Hazard severity
- **LARIAC Buildings 2020** — existing building footprint polygons

All data is stored in PostgreSQL. The frontend receives real-time progress via Server-Sent Events (SSE).

### 3. RAG Retrieval
When the user selects a building type (SFH, ADU, Guest House), the system:
1. Strips zone prefixes (e.g., `[Q]R3-1` -> `R3`) to identify the base zone
2. Builds a query embedding using OpenAI `text-embedding-3-small`
3. Searches PGVector for the top 10 most relevant LAMC regulatory chunks, filtered by zone
4. Zone filter prevents cross-zone rule contamination

### 4. LLM Assessment
The retrieved regulatory chunks, parcel data, zoning info, and building data are sent to Claude (Anthropic API). Claude returns a structured JSON assessment containing:
- **Buildable** — yes/no determination
- **Confidence score** — 0.0 to 1.0 with letter grade (A/B/C/D)
- **Constraints** — individual rules with citations, confidence levels, and deterministic vs interpretive classification
- **Open questions** — uncertainties the system cannot resolve

Assessments are cached by APN + building type so the same query never hits the LLM twice.

### 5. Visualization
The frontend displays:
- Parcel boundary and building footprints on Google Maps (satellite view)
- Zone designations with coverage status indicators
- Structured constraints table with confidence color coding
- Open questions for professional review

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 + TypeScript + Pinia |
| Mapping | Google Maps JavaScript API |
| Backend | Python + FastAPI |
| Database | PostgreSQL + PGVector |
| Geocoding | Google Maps Geocoding API + LA Centerline Locator |
| LLM (Assessment) | Claude API (Anthropic) |
| LLM (Chat) | GPT-4o (OpenAI) |
| Embeddings | OpenAI text-embedding-3-small |
| Infrastructure | Docker Compose (Postgres), AWS for production |

## Regulatory Coverage

15 LAMC sections ingested (1,243 regulatory chunks):

| Zone | LAMC Section | Coverage |
|------|-------------|----------|
| All | 12.03 | Definitions |
| All | 12.04 | Zone hierarchy |
| RE | 12.07 | Residential Estate |
| RS | 12.07.01 | Suburban |
| R1 | 12.08 | One-Family |
| RU | 12.08.5 | Residential Urban |
| R2 | 12.09 | Two-Family |
| RD | 12.09.1 | Restricted Density |
| RW | 12.09.5 | Residential Waterways |
| R3 | 12.10 | Multiple Dwelling |
| R4 | 12.10.5 | Multiple Dwelling |
| R5 | 12.11 | Multiple Dwelling |
| All | 12.21 / 12.21.1 | Height districts, FAR |
| All | 12.22 | Exceptions, ADU rules |

## Production Architecture

For production deployment on AWS:

```
                    +-------------+
                    |  CloudFront |
                    |  (CDN)      |
                    +------+------+
                           |
              +------------+------------+
              |                         |
      +-------+-------+        +-------+-------+
      |  S3 Bucket    |        |  ALB          |
      |  (Vue SPA)    |        |  (Load Bal.)  |
      +---------------+        +-------+-------+
                                       |
                               +-------+-------+
                               |  ECS Fargate  |
                               |  (FastAPI)    |
                               +-------+-------+
                                       |
                          +------------+------------+
                          |                         |
                  +-------+-------+         +-------+-------+
                  |  RDS Postgres |         |  Secrets Mgr  |
                  |  (PostGIS +   |         |  (API Keys)   |
                  |   PGVector)   |         +---------------+
                  +---------------+
```

- **Frontend**: Vue SPA on S3 + CloudFront
- **Backend**: FastAPI on ECS Fargate (auto-scaling)
- **Database**: RDS PostgreSQL with PGVector extension
- **Secrets**: AWS Secrets Manager for API keys
- **Ingestion**: ECS task (run once per regulatory update)

## Running Locally

### Prerequisites
- Docker Desktop
- Python 3.9+
- Node.js 18+

### Setup

```bash
# 1. Start the database
docker compose up -d

# 2. Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Copy and fill in API keys
cp ../.env.example ../.env
# Edit .env with your keys

# 4. Ingest LAMC regulations
python -m app.ingestion.ingest_lamc --pdf ./data/lamc_pdfs/lamc_all.pdf

# 5. Start the backend
uvicorn app.main:app --reload

# 6. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## Data Sources

| Source | Purpose |
|--------|---------|
| [LA County Parcel API](https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0) | Parcel geometry, APN, lot size, building details |
| [LA City GeoHub - Zoning](https://geohub.lacity.org/search) | Base zone designations |
| [LA City GeoHub - Overlays](https://geohub.lacity.org/search) | HPOZ, Specific Plans, Flood, Fire Hazard |
| [LARIAC Buildings 2020](https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/LARIAC_Buildings_2020/MapServer/0) | Building footprints |
| [LA Administrative Code](https://codelibrary.amlegal.com/codes/los_angeles/latest/overview) | LAMC zoning regulations (ingested via RAG) |
