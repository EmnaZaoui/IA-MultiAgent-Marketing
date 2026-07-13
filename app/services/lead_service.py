from app.extensions import db
from app.models.lead import Lead, LeadStatus
from app.utils.validators import is_valid_email, is_valid_sector, is_consumer_email_domain


def build_lead_payload(row: dict, source: str) -> dict:
    return {
        "company_name": (row.get("company_name") or "").strip(),
        "contact_full_name": (row.get("contact_full_name") or "").strip() or None,
        "contact_email": (row.get("contact_email") or "").strip().lower(),
        "contact_phone": (row.get("contact_phone") or "").strip() or None,
        "website_url": (row.get("website_url") or "").strip() or None,
        "sector": (row.get("sector") or "").strip().upper(),
        "business_type": (row.get("business_type") or "").strip() or None,
        "city": (row.get("city") or "").strip() or None,
        "country": (row.get("country") or "").strip() or None,
        "source": source,
    }


def validate_lead_payload(payload: dict) -> tuple[bool, str]:
    if not payload["company_name"]:
        return False, "company_name manquant"

    ok, msg = is_valid_email(payload["contact_email"])
    if not ok:
        return False, f"Email invalide: {msg}"

    if is_consumer_email_domain(payload["contact_email"]):
        return False, "Email B2C détecté (domaine grand public non autorisé, ex: gmail.com, yahoo.com)"

    ok, msg = is_valid_sector(payload["sector"])
    if not ok:
        return False, msg

    return True, ""


def email_already_exists(email: str) -> bool:
    return db.session.query(Lead.id).filter_by(contact_email=email).first() is not None


def create_lead(payload: dict) -> Lead:
    lead = Lead(status=LeadStatus.LEAD_IMPORTED, **payload)
    db.session.add(lead)
    return lead