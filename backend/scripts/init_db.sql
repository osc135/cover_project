-- Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Parcels
CREATE TABLE IF NOT EXISTS parcels (
    id SERIAL PRIMARY KEY,
    apn VARCHAR(20) UNIQUE NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(100),
    lot_size_sqft DOUBLE PRECISION,
    geometry GEOMETRY(POLYGON, 4326),
    raw_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_parcels_apn ON parcels(apn);
CREATE INDEX IF NOT EXISTS idx_parcels_geometry ON parcels USING GIST(geometry);

-- Buildings
CREATE TABLE IF NOT EXISTS buildings (
    id SERIAL PRIMARY KEY,
    apn VARCHAR(20) NOT NULL REFERENCES parcels(apn),
    building_type VARCHAR(50),
    sqft DOUBLE PRECISION,
    geometry GEOMETRY(POLYGON, 4326),
    raw_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_buildings_apn ON buildings(apn);

-- Zoning designations
CREATE TABLE IF NOT EXISTS zoning_designations (
    id SERIAL PRIMARY KEY,
    apn VARCHAR(20) UNIQUE NOT NULL REFERENCES parcels(apn),
    base_zone VARCHAR(20),
    height_district VARCHAR(20),
    hillside BOOLEAN DEFAULT FALSE,
    coastal_zone BOOLEAN DEFAULT FALSE,
    fire_hazard VARCHAR(50),
    hpoz BOOLEAN DEFAULT FALSE,
    specific_plan VARCHAR(100),
    flood_zone VARCHAR(20),
    raw_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_zoning_apn ON zoning_designations(apn);

-- Regulatory chunks (RAG)
CREATE TABLE IF NOT EXISTS regulatory_chunks (
    id SERIAL PRIMARY KEY,
    section_id VARCHAR(20) NOT NULL,
    zone VARCHAR(20),
    topic VARCHAR(100),
    text TEXT NOT NULL,
    source_url TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_chunks_zone ON regulatory_chunks(zone);

-- Assessments
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    apn VARCHAR(20) NOT NULL REFERENCES parcels(apn),
    building_type VARCHAR(20) NOT NULL,
    buildable BOOLEAN,
    confidence_score DOUBLE PRECISION,
    confidence_grade CHAR(1),
    summary TEXT,
    constraints JSONB,
    open_questions JSONB,
    raw_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(apn, building_type)
);
CREATE INDEX IF NOT EXISTS idx_assessments_apn_type ON assessments(apn, building_type);
