# AI Multi Agent Marketing System Fastriom

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Summary](#2-architecture-summary)
3. [Technology Stack](#3-technology-stack)
4. [Prerequisites](#4-prerequisites)
5. [Project Structure](#5-project-structure)
6. [Database Setup (PostgreSQL)](#6-database-setup-postgresql)
7. [Backend Setup (Flask API)](#7-backend-setup-flask-api)
8. [External Services Setup](#8-external-services-setup)
9. [Environment Variables Reference](#9-environment-variables-reference)
10. [Frontend Setup (Angular Dashboard)](#10-frontend-setup-angular-dashboard)
11. [Running the Application](#11-running-the-application)
12. [The Multi-Agent Pipeline Explained](#12-the-multi-agent-pipeline-explained)
13. [API Reference](#13-api-reference)
14. [Email Sending Modes (Safety)](#14-email-sending-modes-safety)
15. [Configuration Files](#15-configuration-files)

---

## 1. Project Overview

This project is an automated, multi-agent B2B prospecting and outbound marketing
platform built for **Fastriom**, a point of sale digitalization solution for the
hospitality, restaurant (CHR), and retail sectors.

The system autonomously performs four sequential tasks that traditionally require
hours of manual work:

1. **Lead discovery** searches the web for businesses matching Fastriom's target
   customer profile (independent restaurants, cafes, bakeries, retail boutiques).
2. **Lead enrichment** scrapes each prospect's website to understand their
   business identity.
3. **Email generation** a chain of specialized AI agents identifies the
   prospect's operational pain points, matches them to relevant Fastriom
   features via a RAG (Retrieval-Augmented Generation) knowledge base, drafts a
   personalized cold email, and runs it through an automated quality-assurance
   review loop before approval.
4. **Email delivery** sends approved emails through a secure SMTP pipeline with
   randomized delays to protect sender domain reputation, and tracks opens,
   clicks, bounces, and unsubscribes.

All four stages can be triggered individually through the API, or executed as one
continuous automated cycle via a single pipeline endpoint.

The system is built to run entirely on free tier / self-hosted infrastructure: no
paid API keys are required for the core functionality (local LLM via Ollama, free
search API tier via Serper, standard SMTP for email delivery).

---

## 2. Architecture Summary

The backend follows a modular, layered structure:

- **Routes** (`app/routes/`): Flask blueprints exposing REST endpoints.
- **Services** (`app/services/`): business logic (scraping, search, email
  sending, campaign orchestration).
- **Agents** (`app/agents/`): the LangGraph multi-agent pipeline that generates
  outbound emails.
- **Models** (`app/models/`): SQLAlchemy ORM models mapped onto the PostgreSQL
  schema.

The multi agent email generation pipeline is implemented with **LangGraph**. Each agent is a graph node operating on a
shared state object, connected through edges that define execution order,
including a conditional loop between the Copywriter and Quality Assurance nodes.

Long running operations (full pipeline execution, batch email sending) are
executed in background threads so that API calls return immediately with a
tracking identifier, rather than blocking the HTTP request until completion.

The frontend is a separate Angular single page application that communicates
with the Flask API over HTTP/CORS.

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Backend framework | Flask 3 (Python) |
| Database | PostgreSQL |
| ORM | Flask-SQLAlchemy |
| Agent orchestration | LangGraph |
| LLM inference | Ollama (local, self-hosted) model: `llama3.1` |
| Vector database (RAG) | ChromaDB (embedded, local persistence) |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, local, no API key) |
| Web search | Serper.dev API (Google Search results, free tier) |
| Web scraping | `requests` + `BeautifulSoup4` |
| Email delivery | Python `smtplib` (SMTP over TLS) |
| API documentation | Swagger UI (`flask-swagger-ui`) with a hand-written OpenAPI spec |
| Frontend framework | Angular |
| Frontend styling | SCSS, custom design system (no external UI library) |

No paid API keys are required to run this project end to end.

---

## 4. Prerequisites

Install the following on your machine before starting:

- **Python 3.12** (a virtual environment will be created from this)
- **PostgreSQL** (version 14 or later recommended), running locally
- **Node.js** (LTS version) and **npm**, for the Angular frontend
- **Angular CLI** (`npm install -g @angular/cli`)
- **Ollama** (for local LLM inference) https://ollama.com
- **Git**, to clone the repository

---

## 5. Project Structure

```
AI_MultiAgent_Marketing/
├── .env                          # Environment variables (not committed to git)
├── .gitignore
├── requirements.txt              # Python dependencies
├── config.py                     # Flask configuration loader
├── run.py                        # Application entry point
├── app/
│   ├── __init__.py                # Application factory (create_app)
│   ├── extensions.py               # SQLAlchemy instance
│   ├── static/
│   │   └── openapi.json            # Hand-written OpenAPI spec for Swagger UI
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── lead.py
│   │   ├── tracking.py
│   │   ├── email_draft.py
│   │   ├── email_send.py
│   │   ├── suppression.py
│   │   └── pipeline_run.py
│   ├── routes/                     # Flask blueprints (API endpoints)
│   │   ├── ingestion.py
│   │   ├── webhooks.py
│   │   ├── enrichment.py
│   │   ├── lead_search.py
│   │   ├── agent_pipeline.py
│   │   ├── campaigns.py
│   │   ├── tracking.py
│   │   └── delivery_webhooks.py
│   ├── services/                   # Business logic
│   │   ├── csv_parser.py
│   │   ├── lead_service.py
│   │   ├── scraper_service.py
│   │   ├── vectorstore_service.py
│   │   ├── enrichment_service.py
│   │   ├── search_provider.py
│   │   ├── lead_search_service.py
│   │   ├── pipeline_orchestrator.py
│   │   ├── smtp_service.py
│   │   ├── tracking_service.py
│   │   └── campaign_service.py
│   ├── agents/                     # LangGraph multi-agent pipeline
│   │   ├── state.py
│   │   ├── prompts.py
│   │   ├── prospecting_prompts.py
│   │   ├── llm_client.py
│   │   ├── nodes.py
│   │   └── graph.py
│   └── utils/
│       ├── validators.py
│       └── logger.py
├── config/
│   └── search_targets.json         # Lead-search targeting profile (ICP)
├── database/
│   ├── schema.sql                  # Initial database schema

├── data/
│   ├── uploads/                    # CSV upload staging directory
│   ├── exports/                    # Lead-search session logs (CSV + JSON)
│   └── chroma_fastriom_kb/         # ChromaDB persistent vector store
├── scripts/
│   ├── ingest_knowledge_base.py
│   ├── run_lead_search.py
│   ├── run_full_pipeline.py
│   ├── run_edge_case_evaluation.py
│   └── run_production_batch.py
├── tests/
│   └── test_csv_parser.py
└── fastriom-dashboard/              # Angular frontend (separate npm project)
    └── src/
        ├── environments/
        ├── assets/
        └── app/
```

---

## 6. Database Setup (PostgreSQL)

### 6.1 Create the database and role

Connect to PostgreSQL as a superuser (typically `postgres`) and run:

```sql
CREATE ROLE fastriom_user WITH LOGIN PASSWORD 'fastriom_pass';
CREATE DATABASE fastriom_marketing_db OWNER fastriom_user;
GRANT ALL PRIVILEGES ON DATABASE fastriom_marketing_db TO fastriom_user;
```

Adjust the username and password to your own preference; the values above match
the defaults used elsewhere in this document. If you change them, update the
`DATABASE_URL` value in your `.env` file accordingly.

### 6.2 Apply the initial schema

database/schema.sql:

```bash
psql -U fastriom_user -d fastriom_marketing_db -h localhost -f database/schema.sql
```

### 6.3 Verify the schema

```sql
\c fastriom_marketing_db
\dt
```

You should see the following tables: `leads`, `lead_status_history`,
`csv_import_batches`, `webhook_events`, `email_drafts`, `pipeline_runs`,
`email_sends`, `suppression_list`, `campaign_runs`.

---

## 7. Backend Setup (Flask API)

### 7.1 Clone the repository and create a virtual environment

```bash
git clone <repository-url> AI_MultiAgent_Marketing
cd AI_MultiAgent_Marketing
python -m venv venv
```

Activate the virtual environment:

- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

### 7.2 Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify there are no dependency conflicts:

```bash
pip check
```

### 7.3 Create the `.env` file

Copy the template provided in [Section 9](#9-environment-variables-reference)
into a file named `.env` in the project root, and fill in the values as
described there.

### 7.4 Build the RAG knowledge base

The system uses a local vector store (ChromaDB) containing Fastriom's product
feature documentation, used by the Strategist agent to match prospect pain
points to relevant features. The source documents live in
`data/knowledge_base/` as Markdown files.

Run the ingestion script once (and again any time the knowledge base content
changes):

```bash
python scripts/ingest_knowledge_base.py
```

Expected output: a summary showing the number of files processed and text
chunks indexed into the local Chroma collection stored under
`data/chroma_fastriom_kb/`.

### 7.5 Start the Flask development server

```bash
flask run
```

The API will be available at `http://localhost:5000`. A basic health check is
available at `http://localhost:5000/health`.

Interactive API documentation (Swagger UI) is available at
`http://localhost:5000/api/docs`.

---

## 8. External Services Setup

### 8.1 Ollama (local LLM inference)

The multi-agent email-generation pipeline and the lead-qualification agent both
require a chat-completion LLM. This project uses **Ollama** to run the model
entirely locally, at no cost and with no external API dependency.

1. Install Ollama from https://ollama.com for your operating system.
2. Pull the model used by this project:

   ```bash
   ollama pull llama3.1
   ```

3. Start the Ollama server:

   ```bash
   ollama serve
   ```

4. Confirm the server is reachable and the model is available:

   ```bash
   curl http://localhost:11434/api/tags
   ```

   The response should list `llama3.1` among the installed models.

**Important:** confirm which port Ollama is actually listening on before
configuring `.env` depending on your installation, the default port may be
`11434`, but a background Ollama service and a manually started one can end up
listening on different ports simultaneously (`11434` vs `11435` have both been
observed in this project's development history). Always verify with `curl`
against the exact port before troubleshooting any "Ollama unreachable" error.

The system also supports **Groq** as a cloud-based, free-tier alternative LLM
provider (faster inference, but subject to daily rate limits). Both providers
share the same code path; switching between them is a matter of changing the
`LLM_PROVIDER` value in `.env` (see Section 9). This project's default and
tested configuration is Ollama.

### 8.2 Serper.dev (web search)

Automated lead discovery requires a search-engine API to find candidate
prospect websites. This project uses **Serper.dev**, which provides Google
Search results through a simple REST API with a free tier (2,500 free queries
on signup, no credit card required).

1. Sign up at https://serper.dev.
2. Copy your API key from the dashboard.
3. Set `SERPER_API_KEY` in `.env`.

A DuckDuckGo-based fallback search method exists in the codebase for reference,
but is not reliable for production use, since DuckDuckGo actively blocks
automated, non official access to its search results. Serper is the primary
and recommended search provider.

### 8.3 SMTP (email delivery)

Outbound email delivery uses standard SMTP over TLS via Python's built-in
`smtplib` no third-party email API or paid service is required.

Using Gmail as an example provider:

1. Enable 2-Step Verification on the sending Google account.
2. Generate an App Password at https://myaccount.google.com/apppasswords.
3. Use that generated password (not your regular account password) as
   `SMTP_PASSWORD` in `.env`.

Any standard SMTP provider (Outlook, a company mail server, a transactional
SMTP relay, etc.) can be used instead by adjusting `SMTP_HOST` and `SMTP_PORT`
accordingly.

---

## 9. Environment Variables Reference

Create a `.env` file in the project root with the following keys.

```env
# Flask
FLASK_APP=run.py
FLASK_DEBUG=1
SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=postgresql://fastriom_user:fastriom_pass@localhost:5432/fastriom_marketing_db

# File upload handling
UPLOAD_FOLDER=data/uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=csv

# Inbound webhook authentication
WEBHOOK_SECRET_TOKEN=change-me-webhook-token

# Vector store (RAG knowledge base)
CHROMA_PERSIST_DIR=data/chroma_fastriom_kb

# LLM provider selection: "ollama" or "groq"
LLM_PROVIDER=ollama

# Ollama configuration (used when LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Groq configuration (used when LLM_PROVIDER=groq; optional cloud alternative)
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant

# Maximum number of copywriter/QA revision cycles per email
LLM_MAX_RETRIES_CRITIQUE=3

# Web search provider for lead discovery
SEARCH_PROVIDER=serper
SERPER_API_KEY=your-serper-api-key-here

# SMTP outbound email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-sending-address@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_FROM_NAME=Fastriom Sales
SMTP_FROM_EMAIL=your-sending-address@gmail.com

# Email tracking base URL (must be reachable by email recipients for
# open/click tracking to work outside of local testing)
BASE_TRACKING_URL=http://localhost:5000

# Email delivery protection: randomized delay range between sends, in seconds
DELIVERY_DELAY_MIN_SECONDS=120
DELIVERY_DELAY_MAX_SECONDS=420

# Email send mode: "dry_run", "sandbox", or "production" see Section 14
EMAIL_SEND_MODE=dry_run
DRY_RUN_REDIRECT_EMAIL=your-own-test-address@example.com
```

Never commit the `.env` file to version control. A `.gitignore` entry for
`.env` is already included in the repository.

---

## 10. Frontend Setup (Angular Dashboard)

The dashboard is a separate Angular application located in the
`fastriom-dashboard/` directory (or cloned as a sibling project, depending on
repository organization).

### 10.1 Install dependencies

```bash
cd fastriom-dashboard
npm install
```

### 10.2 Configure the API endpoint

Edit `src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api/v1',
  swaggerUrl: 'http://localhost:5000/api/docs'
};
```

Adjust `apiUrl` if the Flask backend runs on a different host or port.

### 10.3 Add brand assets

Place the following image files in `src/assets/` before running the
application, so the header displays correctly:

- `logo-tocodepro.png`
- `logo-fastriom.png`

If these files are absent, the header falls back to a styled text label
automatically; the application will still run correctly without them.

Brand colors are defined as CSS custom properties in `src/styles.scss`
(`--color-primary`, `--color-accent`). Update these values to match the exact
brand palette if needed.

### 10.4 Start the development server

```bash
ng serve
```

The dashboard will be available at `http://localhost:4200`.

### 10.5 CORS requirement

The Flask backend must have CORS enabled for the Angular origin
(`http://localhost:4200`) for the dashboard to communicate with the API. This
is already configured in `app/__init__.py` via `flask-cors`; no additional
setup is required as long as both the backend and frontend are running on
their default ports described above.

---

## 11. Running the Application

A complete local run requires four processes running simultaneously, each in
its own terminal:

1. **PostgreSQL**: typically running as a system service; verify it is
   active before starting the backend.
2. **Ollama**: `ollama serve` (skip if already running as a background
   service; confirm the listening port as described in Section 8.1).
3. **Flask backend**:

   ```bash
   cd AI_MultiAgent_Marketing
   venv\Scripts\activate    # or: source venv/bin/activate
   flask run
   ```

4. **Angular frontend**:

   ```bash
   cd fastriom-dashboard
   ng serve
   ```

Once all four are running, open `http://localhost:4200` to access the
dashboard.

---

## 12. The Multi-Agent Pipeline Explained

### 12.1 Lead discovery (Prospector agent)

Given a search query (for example, "restaurants Paris") and a business-type
hint, the system:

1. Queries the Serper web search API for candidate business websites.
2. Filters out known non-viable domains (social media platforms, travel
   aggregators, review sites) that never yield a directly contactable,
   independent business.
3. Scrapes each remaining candidate's homepage via HTTP.
4. Sends the scraped content to the LLM, which determines whether the site
   represents a genuine, independent CHR or Retail business (as opposed to
   editorial content, a large hotel chain, or a directory listing), and
   extracts structured company information.
5. Extracts any visible email address from the scraped page.
6. Validates and deduplicates the resulting lead, then stores it in
   PostgreSQL with `source = AGENT_SEARCH`.

Every candidate processed during a search session whether it results in a
new lead or is rejected is logged with its outcome and reasoning to both a
CSV and a JSON file under `data/exports/`, providing full traceability of the
discovery process independent of the database.

The set of locations and business types targeted by automated discovery is
defined in `config/search_targets.json` (see Section 15).

### 12.2 Enrichment (Researcher tool)

For a given lead with a known website URL, the system scrapes the homepage and
"About" page (if discoverable), extracting clean text content while stripping
scripts, styles, and other non-content markup, and truncating the result to
protect the LLM context window from oversized pages.

### 12.3 Email generation (LangGraph agent graph)

Once a lead is enriched, it enters a four-agent LangGraph pipeline:

1. **Researcher**: summarizes the prospect's business identity from the
   scraped website content.
2. **Strategist**: identifies 2 to 4 plausible operational friction points
   for the prospect's sector, then performs a semantic search (RAG) against
   the Fastriom feature knowledge base to retrieve the most relevant product
   capabilities addressing those friction points.
3. **Copywriter**: drafts a short, personalized cold email using an AIDA or
   PAS framework, connecting the identified friction points to the matched
   Fastriom features, ending with a single clear call to action.
4. **Compliance Officer (QA)**: reviews the drafted email against strict
   criteria (no unfilled placeholders, no grammar issues, no overly
   salesy tone, single clear CTA, no unsupported claims) and either approves
   it or rejects it with specific, actionable feedback.

If the Compliance Officer rejects the draft, the state is routed back to the
Copywriter with the rejection feedback, and the cycle repeats up to
`LLM_MAX_RETRIES_CRITIQUE` times (configurable in `.env`). If the maximum is
reached without approval, the lead is marked `FAILED` with the last rejection
reason recorded. Every revision, including its QA feedback, is stored in the
`email_drafts.revision_history` field for full auditability.

### 12.4 Delivery (Campaign service)

Approved, `DRAFTED` leads that are not present in the suppression list are
eligible for sending. The batch-send process:

1. Generates a unique tracking token per email.
2. Injects an invisible open-tracking pixel and an unsubscribe link into the
   HTML body.
3. Sends the email via SMTP, honoring the configured `EMAIL_SEND_MODE` (see
   Section 14).
4. Waits a randomized delay (`DELIVERY_DELAY_MIN_SECONDS` to
   `DELIVERY_DELAY_MAX_SECONDS`) before the next send, to avoid burst-sending
   patterns that damage sender domain reputation.
5. Records the outcome, and updates the lead's status to `SENT` or `FAILED`.

Recipient opens, clicks, unsubscribes, and asynchronous bounce notifications
are each captured via dedicated tracking/webhook endpoints, and any bounce or
unsubscribe event immediately adds the recipient's email address to the
suppression list, which is checked before every future send.

### 12.5 Full pipeline orchestration

The four stages above can be triggered individually, or as a single
background-executed cycle: discovery across all configured search targets,
followed by enrichment of all newly imported leads, followed by email
generation for all newly enriched leads, followed by delivery of all newly
approved drafts. A `PipelineRun` record tracks the current stage and final
statistics of each execution. A lock prevents starting a new full pipeline run
while one is already in progress.

---

## 13. API Reference

Full interactive documentation is available at `http://localhost:5000/api/docs`
once the backend is running. Key endpoint groups:

| Group | Base path | Purpose |
|---|---|---|
| Leads | `/api/v1/leads` | List, retrieve, import (CSV), and discover leads |
| Webhooks (intake) | `/api/v1/webhooks/lead-intake` | Create leads from external systems |
| Enrichment | `/api/v1/leads/<id>/enrich` | Scrape and enrich a single lead |
| Knowledge base | `/api/v1/knowledge-base/search` | Query the RAG feature knowledge base directly |
| Agents | `/api/v1/leads/<id>/generate-email` | Run the LangGraph email-generation pipeline for one lead |
| Pipeline | `/api/v1/pipeline/run`, `/api/v1/pipeline/run/<id>`, `/api/v1/pipeline/runs` | Trigger and monitor the full automated cycle |
| Campaigns | `/api/v1/campaigns/send-batch`, `/api/v1/campaigns/<id>` | Trigger and monitor a standalone email-send batch |
| Tracking | `/api/v1/track/open/<token>.png`, `/api/v1/track/click/<token>`, `/api/v1/track/unsubscribe/<token>` | Deliverability tracking, consumed by recipient email clients |
| Delivery webhooks | `/api/v1/webhooks/bounce` | Receive asynchronous bounce notifications |

---

## 14. Email Sending Modes (Safety)

To prevent accidental delivery of real emails to real prospects during
development and testing, email sending is governed by the `EMAIL_SEND_MODE`
environment variable, with three possible values:

- **`dry_run`** (default): no email is ever actually sent. The full pipeline
  logic executes normally (draft generation, tracking record creation, status
  updates), but the SMTP call is skipped and replaced with a log entry. This
  is the safe default for local development.

- **`sandbox`**: emails are genuinely sent over SMTP, but every message is
  redirected to the single address configured in `DRY_RUN_REDIRECT_EMAIL`,
  regardless of the lead's actual email address. A warning banner is
  prepended to the email body indicating the original intended recipient.
  Use this mode to visually verify the rendered email, tracking pixel, and
  unsubscribe link in a real inbox without any risk to real prospects.

- **`production`**: emails are sent to their real, intended recipients. This
  mode additionally requires the caller to pass `allow_production_send: true`
  explicitly in the request body to `/api/v1/pipeline/run`; without this
  explicit flag, the sending phase of the full pipeline is skipped even if
  `EMAIL_SEND_MODE` is set to `production`, as a deliberate second safeguard
  against accidental mass sending.

Always verify the current `EMAIL_SEND_MODE` value before triggering the full
pipeline or a batch send.

---

## 15. Configuration Files

### 15.1 `config/search_targets.json`

Defines the Ideal Customer Profile (ICP) targeting used by the automated lead
discovery stage. Structure:

```json
{
  "targets": [
    {"query": "restaurants Paris", "business_type_hint": "restaurant"}
  ],
  "max_results_per_target": 8
}
```

Every entry in `targets` is processed sequentially, in order, on every full
pipeline run there is no rotation or sampling. Adding more entries directly
increases both search coverage and total pipeline run time (each entry
involves multiple search results, each requiring a scrape and an LLM call).
Adjust the list size and `max_results_per_target` according to available time
and API/LLM throughput.

### 15.2 `data/knowledge_base/*.md`

Markdown source files describing Fastriom's product modules and features,
indexed into the RAG vector store. Re-run
`python scripts/ingest_knowledge_base.py` after modifying any file in this
directory for changes to take effect in email generation.

### 15.3 `app/static/openapi.json`

The hand-written OpenAPI 3.0 specification consumed by Swagger UI. When adding
a new API endpoint to the backend, add a corresponding path entry here to keep
the interactive documentation accurate.

---
