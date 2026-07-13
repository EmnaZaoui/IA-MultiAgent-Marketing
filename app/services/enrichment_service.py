from datetime import datetime
from app.extensions import db
from app.models.lead import Lead, LeadStatus
from app.services.scraper_service import WebsiteScraper
from app.utils.validators import is_consumer_email_domain

MAX_RETRIES = 3


def enrich_lead(lead_id: int) -> tuple[dict, int]:
    lead = Lead.query.get(lead_id)
    if lead is None:
        return {"error": "Lead introuvable"}, 404

   
    if is_consumer_email_domain(lead.contact_email):
        lead.status = LeadStatus.FAILED
        lead.error_message = "Email B2C détecté, lead exclu du pipeline"
        db.session.commit()
        return {"lead_id": lead.id, "status": lead.status.value, "reason": lead.error_message}, 200

    if not lead.website_url:
        lead.status = LeadStatus.FAILED
        lead.error_message = "Aucune URL de site web disponible pour l'enrichissement"
        lead.retry_count += 1
        db.session.commit()
        return {"lead_id": lead.id, "status": lead.status.value, "reason": lead.error_message}, 200

    scraper = WebsiteScraper()
    scrape_result = scraper.scrape(lead.website_url)

    if not scrape_result["success"]:
        lead.retry_count += 1
        if lead.retry_count >= MAX_RETRIES:
            lead.status = LeadStatus.FAILED
        lead.error_message = scrape_result["error"]
        db.session.commit()
        return {"lead_id": lead.id, "status": lead.status.value, "error": scrape_result["error"]}, 200

    lead.enriched_data = {
        "title": scrape_result["title"],
        "meta_description": scrape_result["meta_description"],
        "homepage_text": scrape_result["homepage_text"],
        "about_page_url": scrape_result["about_page_url"],
        "about_page_text": scrape_result["about_page_text"],
        "scraped_at": datetime.utcnow().isoformat(),
    }
    lead.status = LeadStatus.ENRICHED
    lead.error_message = None
    db.session.commit()

    return {"lead_id": lead.id, "status": lead.status.value, "enriched_data": lead.enriched_data}, 200