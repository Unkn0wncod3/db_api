-- ================================
-- 1-init_extended.sql — Core Schema 
-- ================================

-- Optional, NUR DEV:
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;

-- ---------- Utility: updated_at automatisch setzen ----------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------- Visibility Level Enum ----------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type WHERE typname = 'visibility_level_enum'
  ) THEN
    CREATE TYPE visibility_level_enum AS ENUM ('admin', 'user');
  END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Users & Roles
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    profile_picture_url TEXT,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);

CREATE TRIGGER trg_users_updated
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Personen
-- ============================================================
CREATE TABLE IF NOT EXISTS persons (
    id SERIAL PRIMARY KEY,

    -- Basic
    first_name        TEXT        NOT NULL DEFAULT 'Unknown',
    last_name         TEXT        NOT NULL DEFAULT 'Unknown',
    date_of_birth     DATE,
    gender            TEXT        NOT NULL DEFAULT 'Unspecified',

    -- Kontakt
    email             TEXT        NOT NULL DEFAULT 'not_provided@example.com',
    phone_number      TEXT        NOT NULL DEFAULT 'N/A',

    -- Adresse (optional feiner aufgeteilt)
    address_line1     TEXT,
    address_line2     TEXT,
    postal_code       TEXT,
    city              TEXT,
    region_state      TEXT,
    country           TEXT,

    -- Admin / Lifecycle
    status            TEXT        NOT NULL DEFAULT 'active', -- active|inactive|archived
    archived_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ,

    -- Optionale Metadaten
    nationality       TEXT,
    occupation        TEXT,
    risk_level        TEXT,                              -- z.B. low|medium|high
    tags              TEXT[] DEFAULT '{}',               -- freie Tagging-Liste
    notes             TEXT,                              -- freie Langnotiz
    metadata          JSONB DEFAULT '{}'::jsonb,         -- flexible Zusatzdaten
    visibility_level  visibility_level_enum NOT NULL DEFAULT 'user'
);

CREATE INDEX IF NOT EXISTS idx_persons_last_first
  ON persons (last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_persons_tags_gin
  ON persons USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_persons_metadata_gin
  ON persons USING GIN (metadata);

CREATE TRIGGER trg_persons_updated
BEFORE UPDATE ON persons
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Notizen (frei)
-- ============================================================
CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    person_id INT REFERENCES persons(id) ON DELETE CASCADE,
    title TEXT,
    text TEXT NOT NULL,
    pinned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    visibility_level visibility_level_enum NOT NULL DEFAULT 'user'
);

CREATE INDEX IF NOT EXISTS idx_notes_person
  ON notes (person_id);
CREATE TRIGGER trg_notes_updated
BEFORE UPDATE ON notes
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Plattformen
-- ============================================================
CREATE TABLE IF NOT EXISTS platforms (
    id SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,        -- "Discord", "Steam", ...
    category     TEXT NOT NULL DEFAULT 'social', -- social|gaming|forum|other
    base_url     TEXT,
    api_base_url TEXT,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ,
    visibility_level visibility_level_enum NOT NULL DEFAULT 'user'
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_platforms_name
  ON platforms (LOWER(name));

CREATE TRIGGER trg_platforms_updated
BEFORE UPDATE ON platforms
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Profile (Konto auf einer Plattform)
-- ============================================================
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    platform_id    INT NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    username       TEXT NOT NULL,
    external_id    TEXT,
    display_name   TEXT,
    url            TEXT,
    status         TEXT NOT NULL DEFAULT 'active', -- active|inactive|banned|archived

    -- optionale Felder
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ,
    last_seen_at   TIMESTAMPTZ,
    language       TEXT,                 -- z.B. "de", "en"
    region         TEXT,                 -- z.B. "EU", "NA"
    is_verified    BOOLEAN DEFAULT FALSE,
    avatar_url     TEXT,
    bio            TEXT,
    metadata       JSONB DEFAULT '{}'::jsonb,
    visibility_level visibility_level_enum NOT NULL DEFAULT 'user'
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_profiles_platform_username
  ON profiles (platform_id, LOWER(username));
CREATE INDEX IF NOT EXISTS idx_profiles_external
  ON profiles (platform_id, external_id);
CREATE INDEX IF NOT EXISTS idx_profiles_last_seen
  ON profiles (last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_profiles_metadata_gin
  ON profiles USING GIN (metadata);

CREATE TRIGGER trg_profiles_updated
BEFORE UPDATE ON profiles
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Zuordnung Person <-> Profile (Many-to-Many)
-- ============================================================
CREATE TABLE IF NOT EXISTS person_profile_map (
    person_id   INT NOT NULL REFERENCES persons(id)   ON DELETE CASCADE,
    profile_id  INT NOT NULL REFERENCES profiles(id)  ON DELETE CASCADE,
    linked_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    note        TEXT,
    visibility_level visibility_level_enum NOT NULL DEFAULT 'user',
    PRIMARY KEY (person_id, profile_id)
);

-- ============================================================
-- Fahrzeuge
-- ============================================================
CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    label          TEXT NOT NULL,     -- "Car XY"
    make           TEXT,
    model          TEXT,
    build_year     INT,
    license_plate  TEXT,
    vin            TEXT,
    vehicle_type   TEXT,              -- car|truck|van|bike|other
    energy_type    TEXT,              -- petrol|diesel|electric|hybrid|other
    color          TEXT,
    mileage_km     INT,
    last_service_at TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ,
    metadata       JSONB DEFAULT '{}'::jsonb,
    visibility_level visibility_level_enum NOT NULL DEFAULT 'user'
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_vehicles_license_plate
  ON vehicles (license_plate) WHERE license_plate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_vehicles_type_energy
  ON vehicles (vehicle_type, energy_type);
CREATE INDEX IF NOT EXISTS idx_vehicles_metadata_gin
  ON vehicles USING GIN (metadata);

CREATE TRIGGER trg_vehicles_updated
BEFORE UPDATE ON vehicles
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Aktivitäten / Verlauf
-- ============================================================
CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    person_id     INT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL,                -- z.B. drive|login|post|join_community|custom
    occurred_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- optionale Targets
    vehicle_id    INT REFERENCES vehicles(id)    ON DELETE SET NULL,
    profile_id    INT REFERENCES profiles(id)    ON DELETE SET NULL,

    item          TEXT,
    notes         TEXT,
    details       JSONB DEFAULT '{}'::jsonb,     -- flexible Zusatzdaten

    -- optionale Kontextfelder
    severity      TEXT,                          -- info|warn|error|critical
    source        TEXT,                          -- manual|api|import|system
    ip_address    INET,
    user_agent    TEXT,
    geo_location  TEXT,                          -- "Berlin, DE" o.ä.
    created_by    TEXT,                          -- Benutzername/System
    updated_at    TIMESTAMPTZ,
    visibility_level visibility_level_enum NOT NULL DEFAULT 'user',

    -- Mindestens EIN Target-Feld sollte befüllt sein
    CONSTRAINT chk_activities_target CHECK (
        vehicle_id IS NOT NULL OR profile_id IS NOT NULL OR item IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_activities_person_time
  ON activities (person_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_activities_gin_details
  ON activities USING GIN (details);
CREATE INDEX IF NOT EXISTS idx_activities_severity
  ON activities (severity);

CREATE TRIGGER trg_activities_updated
BEFORE UPDATE ON activities
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- Nützliche Views
-- ============================================================

-- 1) Vereinfachter Verlauf je Person
CREATE OR REPLACE VIEW v_person_timeline AS
SELECT
  a.id AS activity_id,
  a.occurred_at,
  per.id AS person_id,
  per.first_name || ' ' || per.last_name AS person_name,
  a.activity_type,
  COALESCE(v.label, pr.username, a.item, 'N/A') AS target,
  a.severity,
  a.source,
  a.geo_location,
  a.notes,
  a.details,
  per.visibility_level AS person_visibility_level,
  a.visibility_level   AS activity_visibility_level
FROM activities a
JOIN persons per ON per.id = a.person_id
LEFT JOIN vehicles v ON v.id = a.vehicle_id
LEFT JOIN profiles pr ON pr.id = a.profile_id;

-- 2) Schneller Überblick über Profile einer Person
CREATE OR REPLACE VIEW v_person_profiles AS
SELECT
  ppm.person_id,
  pf.name        AS platform,
  pr.username,
  pr.display_name,
  pr.status,
  pr.last_seen_at,
  pr.url,
  ppm.visibility_level AS link_visibility_level,
  pr.visibility_level  AS profile_visibility_level,
  pf.visibility_level  AS platform_visibility_level,
  per.visibility_level AS person_visibility_level
FROM person_profile_map ppm
JOIN persons per ON per.id = ppm.person_id
JOIN profiles pr  ON pr.id = ppm.profile_id
JOIN platforms pf ON pf.id = pr.platform_id;

-- 3) Personen-Summary mit Anzahl verknüpfter Entitäten
CREATE OR REPLACE VIEW v_person_summary AS
SELECT
  p.id AS person_id,
  p.first_name || ' ' || p.last_name AS person_name,
  p.email,
  p.status,
  p.visibility_level,
  COUNT(DISTINCT ppm.profile_id)    AS profiles_count,
  COUNT(DISTINCT a.id)              AS activities_count,
  COUNT(DISTINCT n.id)              AS notes_count
FROM persons p
LEFT JOIN person_profile_map ppm ON ppm.person_id = p.id
LEFT JOIN activities a          ON a.person_id   = p.id
LEFT JOIN notes n               ON n.person_id   = p.id
GROUP BY p.id, p.first_name, p.last_name, p.email, p.status, p.visibility_level;
