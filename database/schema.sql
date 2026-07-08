-- =========================================================
-- SCHEMA: AI_MultiAgent_Marketing - Sprint 1
-- Suivi des états: LEAD_IMPORTED -> ENRICHED -> DRAFTED -> SENT / FAILED
-- =========================================================

-- 1. Type ENUM pour les statuts du pipeline
DROP TYPE IF EXISTS lead_status CASCADE;
CREATE TYPE lead_status AS ENUM (
    'LEAD_IMPORTED',
    'ENRICHED',
    'DRAFTED',
    'SENT',
    'FAILED'
);

-- 2. Table principale des leads
CREATE TABLE IF NOT EXISTS leads (
    id                  SERIAL PRIMARY KEY,
    company_name        VARCHAR(255) NOT NULL,
    contact_full_name   VARCHAR(255),
    contact_email       VARCHAR(255) NOT NULL UNIQUE,
    contact_phone       VARCHAR(50),
    website_url         VARCHAR(500),
    sector              VARCHAR(50) NOT NULL CHECK (sector IN ('CHR', 'RETAIL', 'OTHER')),
    business_type       VARCHAR(100),          -- ex: restaurant, boulangerie, boutique_vetements
    city                VARCHAR(100),
    country             VARCHAR(100),
    source              VARCHAR(50) NOT NULL DEFAULT 'CSV_IMPORT', -- CSV_IMPORT | WEBHOOK | MANUAL
    status              lead_status NOT NULL DEFAULT 'LEAD_IMPORTED',
    enriched_data       JSONB DEFAULT '{}'::jsonb,   -- rempli au Sprint 2/3 par l'agent Researcher
    error_message       TEXT,
    retry_count         INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_leads_status  ON leads(status);
CREATE INDEX idx_leads_sector  ON leads(sector);
CREATE INDEX idx_leads_email   ON leads(contact_email);

-- 3. Historique des changements de statut (audit trail)
CREATE TABLE IF NOT EXISTS lead_status_history (
    id              SERIAL PRIMARY KEY,
    lead_id         INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    previous_status lead_status,
    new_status      lead_status NOT NULL,
    note            TEXT,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_history_lead_id ON lead_status_history(lead_id);

-- 4. Suivi des batchs d'import CSV
CREATE TABLE IF NOT EXISTS csv_import_batches (
    id              SERIAL PRIMARY KEY,
    filename        VARCHAR(255) NOT NULL,
    total_rows      INTEGER NOT NULL DEFAULT 0,
    imported_rows   INTEGER NOT NULL DEFAULT 0,
    duplicate_rows  INTEGER NOT NULL DEFAULT 0,
    failed_rows     INTEGER NOT NULL DEFAULT 0,
    status          VARCHAR(50) NOT NULL DEFAULT 'PROCESSING', -- PROCESSING | COMPLETED | FAILED
    error_details    JSONB DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ
);

-- 5. Journal des événements webhook entrants (intake + futurs événements de deliverabilité Sprint 4)
CREATE TABLE IF NOT EXISTS webhook_events (
    id              SERIAL PRIMARY KEY,
    event_type      VARCHAR(50) NOT NULL,  -- LEAD_INTAKE | OPENED | CLICKED | BOUNCED | UNSUBSCRIBED
    payload         JSONB NOT NULL,
    lead_id         INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    processed       BOOLEAN NOT NULL DEFAULT false,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_webhook_events_type ON webhook_events(event_type);

-- 6. Trigger: mise à jour automatique de updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_leads_updated_at ON leads;
CREATE TRIGGER trg_leads_updated_at
BEFORE UPDATE ON leads
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 7. Trigger: journalisation automatique des changements de statut
CREATE OR REPLACE FUNCTION log_lead_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO lead_status_history(lead_id, previous_status, new_status, note)
        VALUES (NEW.id, NULL, NEW.status, 'Création du lead');
    ELSIF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) THEN
        INSERT INTO lead_status_history(lead_id, previous_status, new_status, note)
        VALUES (NEW.id, OLD.status, NEW.status, 'Changement automatique de statut');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_leads_status_history ON leads;
CREATE TRIGGER trg_leads_status_history
AFTER INSERT OR UPDATE ON leads
FOR EACH ROW EXECUTE FUNCTION log_lead_status_change();