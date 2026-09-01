-- =========================================================
-- SCHEMA: AI_MultiAgent_Marketing
-- Consolidated schema — covers Sprint 1 through Sprint 4.
-- This is the single file to run on a fresh database; the
-- individual migration files under database/migrations/ are
-- kept for historical reference only and do not need to be
-- run separately when starting from this file.
--
-- Lead lifecycle: LEAD_IMPORTED -> ENRICHED -> DRAFTED -> SENT / FAILED
-- =========================================================


-- =========================================================
-- SPRINT 1: Core infrastructure and ingestion
-- =========================================================

-- 1. ENUM type for the lead pipeline status
DROP TYPE IF EXISTS lead_status CASCADE;
CREATE TYPE lead_status AS ENUM (
    'LEAD_IMPORTED',
    'ENRICHED',
    'DRAFTED',
    'SENT',
    'FAILED'
);

-- 2. Main leads table
CREATE TABLE IF NOT EXISTS leads (
    id                  SERIAL PRIMARY KEY,
    company_name        VARCHAR(255) NOT NULL,
    contact_full_name   VARCHAR(255),
    contact_email       VARCHAR(255) NOT NULL UNIQUE,
    contact_phone       VARCHAR(50),
    website_url         VARCHAR(500),
    sector              VARCHAR(50) NOT NULL CHECK (sector IN ('CHR', 'RETAIL', 'OTHER')),
    business_type       VARCHAR(100),          -- e.g. restaurant, boulangerie, boutique_vetements
    city                VARCHAR(100),
    country             VARCHAR(100),
    source              VARCHAR(50) NOT NULL DEFAULT 'CSV_IMPORT', -- CSV_IMPORT | WEBHOOK | AGENT_SEARCH | MANUAL
    status              lead_status NOT NULL DEFAULT 'LEAD_IMPORTED',
    enriched_data       JSONB DEFAULT '{}'::jsonb,   -- populated by the Researcher agent (Sprint 2/3)
    error_message       TEXT,
    retry_count         INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_leads_status  ON leads(status);
CREATE INDEX idx_leads_sector  ON leads(sector);
CREATE INDEX idx_leads_email   ON leads(contact_email);

-- 3. Status change audit trail
CREATE TABLE IF NOT EXISTS lead_status_history (
    id              SERIAL PRIMARY KEY,
    lead_id         INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    previous_status lead_status,
    new_status      lead_status NOT NULL,
    note            TEXT,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_history_lead_id ON lead_status_history(lead_id);

-- 4. Bulk CSV import batch tracking
CREATE TABLE IF NOT EXISTS csv_import_batches (
    id              SERIAL PRIMARY KEY,
    filename        VARCHAR(255) NOT NULL,
    total_rows      INTEGER NOT NULL DEFAULT 0,
    imported_rows   INTEGER NOT NULL DEFAULT 0,
    duplicate_rows  INTEGER NOT NULL DEFAULT 0,
    failed_rows     INTEGER NOT NULL DEFAULT 0,
    status          VARCHAR(50) NOT NULL DEFAULT 'PROCESSING', -- PROCESSING | COMPLETED | FAILED
    error_details   JSONB DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ
);

-- 5. Inbound webhook event log (lead intake + deliverability events)
CREATE TABLE IF NOT EXISTS webhook_events (
    id              SERIAL PRIMARY KEY,
    event_type      VARCHAR(50) NOT NULL,  -- LEAD_INTAKE | OPENED | CLICKED | BOUNCED | UNSUBSCRIBED
    payload         JSONB NOT NULL,
    lead_id         INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    processed       BOOLEAN NOT NULL DEFAULT false,
    received_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_webhook_events_type ON webhook_events(event_type);

-- 6. Trigger function: auto-update updated_at on row update
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

-- 7. Trigger function: automatic status-change logging
CREATE OR REPLACE FUNCTION log_lead_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO lead_status_history(lead_id, previous_status, new_status, note)
        VALUES (NEW.id, NULL, NEW.status, 'Lead created');
    ELSIF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) THEN
        INSERT INTO lead_status_history(lead_id, previous_status, new_status, note)
        VALUES (NEW.id, OLD.status, NEW.status, 'Automatic status change');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_leads_status_history ON leads;
CREATE TRIGGER trg_leads_status_history
AFTER INSERT OR UPDATE ON leads
FOR EACH ROW EXECUTE FUNCTION log_lead_status_change();


-- =========================================================
-- SPRINT 3: Multi-agent email generation (originally migration 002)
-- =========================================================

CREATE TABLE IF NOT EXISTS email_drafts (
    id                  SERIAL PRIMARY KEY,
    lead_id             INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    subject             VARCHAR(255),
    body                TEXT,
    framework_used      VARCHAR(10),              -- AIDA | PAS
    matched_features    JSONB DEFAULT '[]'::jsonb, -- RAG results used by the Strategist agent
    friction_points     JSONB DEFAULT '[]'::jsonb,
    critique_status     VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING | APPROVED | REJECTED | MAX_RETRIES_EXCEEDED
    critique_feedback   TEXT,
    revision_count      INTEGER NOT NULL DEFAULT 0,
    revision_history    JSONB DEFAULT '[]'::jsonb, -- full history of versions + QA feedback
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_email_drafts_lead_id ON email_drafts(lead_id);
CREATE INDEX idx_email_drafts_status ON email_drafts(critique_status);

DROP TRIGGER IF EXISTS trg_email_drafts_updated_at ON email_drafts;
CREATE TRIGGER trg_email_drafts_updated_at
BEFORE UPDATE ON email_drafts
FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- =========================================================
-- SPRINT 3: Full pipeline orchestration tracking (originally migration 003)
-- =========================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id              SERIAL PRIMARY KEY,
    status          VARCHAR(20) NOT NULL DEFAULT 'RUNNING', -- RUNNING | COMPLETED | FAILED
    triggered_by    VARCHAR(20) NOT NULL DEFAULT 'MANUAL',  -- MANUAL | SCHEDULED
    current_step    VARCHAR(30),                             -- DISCOVERY | ENRICHMENT | EMAIL_GENERATION | SENDING | DONE
    stats           JSONB DEFAULT '{}'::jsonb,
    error_message   TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ
);

CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status);


-- =========================================================
-- SPRINT 4: Email delivery, deliverability tracking, and
-- suppression list (originally migration 004)
-- =========================================================

-- 1. Actual send records (distinct from drafts: a draft can be
--    approved but not yet sent)
CREATE TABLE IF NOT EXISTS email_sends (
    id                  SERIAL PRIMARY KEY,
    lead_id             INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    draft_id            INTEGER REFERENCES email_drafts(id) ON DELETE SET NULL,
    tracking_token      VARCHAR(64) NOT NULL UNIQUE,
    recipient_email     VARCHAR(255) NOT NULL,
    subject             VARCHAR(255),
    send_status         VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING | SENT | SIMULATED | FAILED | SUPPRESSED
    delivery_status     VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN', -- UNKNOWN | OPENED | CLICKED | BOUNCED | UNSUBSCRIBED
    error_message       TEXT,
    opened_at           TIMESTAMPTZ,
    clicked_at          TIMESTAMPTZ,
    bounced_at          TIMESTAMPTZ,
    unsubscribed_at     TIMESTAMPTZ,
    sent_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_email_sends_lead_id ON email_sends(lead_id);
CREATE INDEX idx_email_sends_token ON email_sends(tracking_token);
CREATE INDEX idx_email_sends_status ON email_sends(delivery_status);

-- 2. Suppression list (opt-out automation — any bounce or
--    unsubscribe immediately excludes the address from all
--    future sends)
CREATE TABLE IF NOT EXISTS suppression_list (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    domain          VARCHAR(255) NOT NULL,
    reason          VARCHAR(30) NOT NULL, -- BOUNCED | UNSUBSCRIBED | MANUAL
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_suppression_email ON suppression_list(email);
CREATE INDEX idx_suppression_domain ON suppression_list(domain);

-- 3. Batch send campaign tracking
CREATE TABLE IF NOT EXISTS campaign_runs (
    id                  SERIAL PRIMARY KEY,
    status              VARCHAR(20) NOT NULL DEFAULT 'RUNNING', -- RUNNING | COMPLETED | FAILED
    total_targeted      INTEGER NOT NULL DEFAULT 0,
    total_sent          INTEGER NOT NULL DEFAULT 0,
    total_suppressed    INTEGER NOT NULL DEFAULT 0,
    total_failed        INTEGER NOT NULL DEFAULT 0,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ
);


-- =========================================================
-- End of schema. Expected tables after running this file:
-- leads, lead_status_history, csv_import_batches, webhook_events,
-- email_drafts, pipeline_runs, email_sends, suppression_list,
-- campaign_runs
-- =========================================================
