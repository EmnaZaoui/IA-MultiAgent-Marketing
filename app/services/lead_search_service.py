import os
import csv
import json
import logging
from datetime import datetime

from app.extensions import db
from app.models.lead import Lead
from app.services.scraper_service import WebsiteScraper
from app.services.lead_service import validate_lead_payload, email_already_exists, create_lead
from app.services.search_provider import search_web
from app.agents.llm_client import call_llm_json, LLMError
from app.agents.prospecting_prompts import PROSPECTOR_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

EXPORTS_DIR = "data/exports"
MAX_SEARCH_RESULTS_DEFAULT = 10

EXCLUDED_DOMAINS = [
    "tripadvisor.", "thefork.", "facebook.com", "instagram.com",
    "youtube.com", "twitter.com", "x.com", "linkedin.com",
    "wikipedia.org", "pinterest.", "tiktok.com",
]


def _is_excluded_domain(url: str) -> bool:
    url_lower = url.lower()
    return any(domain in url_lower for domain in EXCLUDED_DOMAINS)


def _search_candidate_websites(query: str, max_results: int) -> list:
    """Recherche des sites web candidats via le fournisseur configuré (Serper/DuckDuckGo)."""
    return search_web(query, max_results)


def _extract_lead_info(scrape_result: dict, business_type_hint: str) -> dict | None:
    """Utilise le LLM pour qualifier et structurer les infos du prospect candidat."""
    homepage_text = scrape_result.get("homepage_text") or ""
    if not homepage_text:
        return None

    user_prompt = (
        f"Indice de type d'activité recherché: {business_type_hint}\n"
        f"Titre de la page: {scrape_result.get('title')}\n"
        f"Meta description: {scrape_result.get('meta_description')}\n"
        f"Contenu de la page d'accueil: {homepage_text[:2000]}"
    )

    try:
        return call_llm_json(PROSPECTOR_EXTRACTION_PROMPT, user_prompt, temperature=0.2)
    except LLMError as e:
        logger.error(f"Erreur extraction LLM pour '{scrape_result.get('url')}': {str(e)}")
        return None


def _export_session_log(session_results: list, query: str) -> dict:
    """Exporte TOUT le log de la session (leads créés ou non) en CSV et JSON,
    conformément à la demande de traçabilité complète."""
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c if c.isalnum() else "_" for c in query)[:40]

    json_path = os.path.join(EXPORTS_DIR, f"search_{safe_query}_{timestamp}.json")
    csv_path = os.path.join(EXPORTS_DIR, f"search_{safe_query}_{timestamp}.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(session_results, f, ensure_ascii=False, indent=2)

    if session_results:
        fieldnames = sorted({key for row in session_results for key in row.keys()})
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(session_results)

    return {"json_export": json_path, "csv_export": csv_path}


def discover_leads(query: str, business_type_hint: str = "", max_results: int = MAX_SEARCH_RESULTS_DEFAULT) -> dict:
    """
    Pipeline complet de prospection autonome:
    recherche web -> filtrage plateformes sociales -> scraping -> extraction LLM
    -> validation -> stockage PostgreSQL + export CSV/JSON du log complet.
    """
    scraper = WebsiteScraper()
    raw_candidates = _search_candidate_websites(query, max_results)
    candidates = [c for c in raw_candidates if not _is_excluded_domain(c["url"])]

    session_results = []
    stats = {
        "searched": len(candidates),
        "excluded_platforms": len(raw_candidates) - len(candidates),
        "created": 0,
        "duplicates": 0,
        "irrelevant": 0,
        "no_email": 0,
        "errors": 0,
    }

    for candidate in candidates:
        row = {"url": candidate["url"], "title": candidate["title"], "outcome": None}

        scrape_result = scraper.scrape(candidate["url"])
        if not scrape_result["success"]:
            row["outcome"] = "SCRAPE_FAILED"
            row["error"] = scrape_result["error"]
            stats["errors"] += 1
            session_results.append(row)
            continue

        extracted = _extract_lead_info(scrape_result, business_type_hint)
        if not extracted or not extracted.get("is_relevant_prospect"):
            row["outcome"] = "IRRELEVANT"
            row["reasoning"] = (extracted or {}).get("reasoning", "Extraction LLM échouée")
            stats["irrelevant"] += 1
            session_results.append(row)
            continue

        emails_found = scrape_result.get("emails_found", [])
        if not emails_found:
            row["outcome"] = "NO_EMAIL_FOUND"
            row["company_name"] = extracted.get("company_name")
            row["sector"] = extracted.get("sector")
            row["reasoning"] = extracted.get("reasoning")
            stats["no_email"] += 1
            session_results.append(row)
            continue

        payload = {
            "company_name": extracted.get("company_name") or candidate["title"],
            "contact_full_name": None,
            "contact_email": emails_found[0].strip().lower(),
            "contact_phone": None,
            "website_url": candidate["url"],
            "sector": (extracted.get("sector") or "").strip().upper(),
            "business_type": extracted.get("business_type"),
            "city": extracted.get("city") or None,
            "country": extracted.get("country") or None,
            "source": "AGENT_SEARCH",
        }

        is_valid, error_message = validate_lead_payload(payload)
        if not is_valid:
            row["outcome"] = "VALIDATION_FAILED"
            row["error"] = error_message
            row.update(payload)
            stats["errors"] += 1
            session_results.append(row)
            continue

        if email_already_exists(payload["contact_email"]):
            row["outcome"] = "DUPLICATE"
            row.update(payload)
            stats["duplicates"] += 1
            session_results.append(row)
            continue

        lead = create_lead(payload)
        db.session.flush()

        row["outcome"] = "CREATED"
        row["lead_id"] = lead.id
        row.update(payload)
        stats["created"] += 1
        session_results.append(row)

    db.session.commit()
    export_paths = _export_session_log(session_results, query)

    return {"query": query, "stats": stats, "exports": export_paths, "details": session_results}